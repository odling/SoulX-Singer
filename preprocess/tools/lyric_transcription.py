# https://modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/summary
# https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2
import os
import re
import time
from typing import Any, Dict, List, Tuple

import torch
import librosa
import numpy as np
from funasr import AutoModel


def _build_words_with_gaps(raw_words, raw_timestamps, wav_fn: str):
    words, word_durs = [], []
    prev = 0.0
    for w, t in zip(raw_words, raw_timestamps):
        s, e = float(t[0]), float(t[1])
        if s > prev:
            words.append("<SP>")
            word_durs.append(s - prev)
        words.append(w)
        word_durs.append(e - s)
        prev = e

    wav_len = librosa.get_duration(filename=wav_fn)
    if wav_len > prev:
        if len(words) == 0:
            words.append("<SP>")
            word_durs.append(wav_len)
            return words, word_durs
        if words[-1] != "<SP>":
            words.append("<SP>")
            word_durs.append(wav_len - prev)
        else:
            word_durs[-1] += wav_len - prev

    return words, word_durs

def _word_dur_post_process(words, word_durs, f0):
    """Post-process word durations using f0 to better place silences.
    """
    # f0 time grid parameters
    sr = 24000  # f0 sample rate
    hop_length = 480  # f0 hop length

    # Convert word durations (seconds) to frame boundaries on the f0 grid.
    boundaries = np.cumsum([
        0,
        *[
            int(dur * sr / hop_length)
            for dur in word_durs
        ],
    ]).tolist()

    sil_tolerance = 5   # tolerance frames for silence detection
    ext_tolerance = 5   # tolerance frames for vocal extension

    new_words: list[str] = []
    new_word_durs: list[float] = []
    if words:
        new_words.append(words[0])
        new_word_durs.append(word_durs[0])

    for i in range(1, len(words)):
        word = words[i]
        if word == "<SP>":
            start_frame = boundaries[i]
            end_frame = boundaries[i + 1]

            num_frames = end_frame - start_frame
            frame_idx = start_frame

            # Find first region with at least 5 consecutive "unvoiced" frames.
            unvoiced_count = 0
            while frame_idx < end_frame:
                if f0[frame_idx] <= 1:  # unvoiced
                    unvoiced_count += 1
                    if unvoiced_count >= sil_tolerance:
                        frame_idx -= sil_tolerance - 1  # back to the last voiced frame
                        break
                else:
                    unvoiced_count = 0
                frame_idx += 1

            voice_frames = frame_idx - start_frame

            if voice_frames >= int(num_frames * 0.9):  # over 90% voiced
                # Treat the whole "<SP>" as silence and merge into previous word.
                new_word_durs[-1] += word_durs[i]
            elif voice_frames >= ext_tolerance:  # over 5 frames voiced
                # Split the "<SP>" into two parts: leading silence and tail kept as "<SP>".
                dur = voice_frames * hop_length / sr
                new_word_durs[-1] += dur
                new_words.append("<SP>")
                new_word_durs.append(word_durs[i] - dur)
            else:
                # Too short to adjust, keep as-is.
                new_words.append(word)
                new_word_durs.append(word_durs[i])
        else:
            new_words.append(word)
            new_word_durs.append(word_durs[i])

    return new_words, new_word_durs


class _ASRZhModel:
    """Mandarin/Cantonese ASR wrapper."""

    def __init__(self, model_path: str, device: str):
        self.model = AutoModel(
            model=model_path,
            disable_update=True,
            device=device,
        )

    def process(self, wav_fn):
        out = self.model.generate(wav_fn, output_timestamp=True)[0]
        raw_words = out["text"].replace("@", "").split(" ")
        raw_timestamps = [[t[0] / 1000, t[1] / 1000] for t in out["timestamp"]]
        words, word_durs = _build_words_with_gaps(raw_words, raw_timestamps, wav_fn)

        if os.path.exists(wav_fn.replace(".wav", "_f0.npy")):
            words, word_durs = _word_dur_post_process(
                words, word_durs, np.load(wav_fn.replace(".wav", "_f0.npy"))
            )

        return words, word_durs


def _is_apple_silicon() -> bool:
    """True when running on Apple Silicon (MPS available). NeMo is not supported there."""
    try:
        return bool(torch.backends.mps.is_available())
    except Exception:
        return False


class _ASREnModel:
    """English ASR wrapper - uses Whisper (Apple Silicon compatible) or NeMo as fallback."""

    def __init__(self, model_path: str, device: str):
        self.device = device
        self.model_path = model_path
        self.use_whisper = False
        self.model = None
        use_apple_silicon = _is_apple_silicon()

        # On Apple Silicon use only Whisper (NeMo is not supported)
        # Otherwise try Whisper first, then NeMo
        try:
            import whisper
            # Whisper on MPS can be unstable; use CPU for reliability on Apple Silicon
            load_device = "cpu" if (device == "mps" or use_apple_silicon) else device
            self.model = whisper.load_model("base", device=load_device)
            self.use_whisper = True
            print("[ASR English] Using OpenAI Whisper (Apple Silicon compatible)")
        except ImportError as e:
            if use_apple_silicon:
                raise ImportError(
                    "English ASR on Apple Silicon requires 'openai-whisper'. "
                    "Install it with: pip install openai-whisper"
                ) from e
            # Fall through to try NeMo on non-Apple Silicon
            pass
        except Exception as e:
            if use_apple_silicon:
                # Re-raise so the user sees the real cause (e.g. model download, ffmpeg)
                import sys
                print("English ASR (Whisper) load failed. Ensure: pip install openai-whisper, and ffmpeg installed.", file=sys.stderr)
                raise
            pass

        # Fallback to NeMo only on non-Apple Silicon (NVIDIA / CUDA)
        if not self.use_whisper:
            try:
                import nemo.collections.asr as nemo_asr  # type: ignore
                self.model = nemo_asr.models.ASRModel.restore_from(
                    restore_path=model_path,
                    map_location=device,
                )
                self.model.eval()
                print("[ASR English] Using NeMo Parakeet-TDT")
            except Exception as e:
                raise ImportError(
                    "English ASR requires either 'openai-whisper' or 'nemo_toolkit'. "
                    "For Apple Silicon, install whisper: pip install openai-whisper\n"
                    "For NVIDIA GPUs, install NeMo: pip install nemo_toolkit"
                ) from e

    @staticmethod
    def _clean_word(word: str) -> str:
        return re.sub(r"[\?\.,:]", "", word).strip()

    @staticmethod
    def _extract_word_segments(output: Any) -> List[Dict[str, Any]]:
        ts = getattr(output, "timestamp", None)
        if not ts or not isinstance(ts, dict):
            return []
        word_ts = ts.get("word")
        return word_ts if isinstance(word_ts, list) else []

    def _process_whisper(self, wav_fn: str) -> Tuple[List[str], List[float]]:
        """Process with Whisper model."""
        result = self.model.transcribe(wav_fn, word_timestamps=True, language="en")
        
        raw_words: List[str] = []
        raw_timestamps: List[List[float]] = []
        
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                word = self._clean_word(word_info.get("word", ""))
                if word:
                    raw_words.append(word)
                    raw_timestamps.append([word_info.get("start", 0.0), word_info.get("end", 0.0)])
        
        return raw_words, raw_timestamps

    def _process_nemo(self, wav_fn: str) -> Tuple[List[str], List[float]]:
        """Process with NeMo model."""
        outputs = self.model.transcribe(
            [wav_fn],
            timestamps=True,
            batch_size=1,
            num_workers=0,
        )
        output = outputs[0] if outputs else None

        raw_words: List[str] = []
        raw_timestamps: List[List[float]] = []
        if output is not None:
            for w in self._extract_word_segments(output):
                s, e = float(w.get("start", 0.0)), float(w.get("end", 0.0))
                word = self._clean_word(str(w.get("word", "")))
                if word:
                    raw_words.append(word)
                    raw_timestamps.append([s, e])
        
        return raw_words, raw_timestamps

    def process(self, wav_fn: str) -> Tuple[List[str], List[float]]:
        if self.use_whisper:
            raw_words, raw_timestamps = self._process_whisper(wav_fn)
        else:
            raw_words, raw_timestamps = self._process_nemo(wav_fn)

        words, durs = _build_words_with_gaps(raw_words, raw_timestamps, wav_fn)

        if os.path.exists(wav_fn.replace(".wav", "_f0.npy")):
            words, durs = _word_dur_post_process(
                words, durs, np.load(wav_fn.replace(".wav", "_f0.npy"))
            )

        return words, durs


class LyricTranscriber:
    """Transcribe lyrics from singing voice segment
    """

    def __init__(
        self,
        zh_model_path: str,
        en_model_path: str,
        device: str = "mps",
        *,
        verbose: bool = True,
    ):
        """Initialize lyric transcriber.

        Args:
            zh_model_path (str): Path to the Chinese model file.
            en_model_path (str): Path to the English model file.
            device (str): Device to use for tensor operations.
            verbose (bool): Whether to print verbose logs.
        """
        self.verbose = verbose
        self.device = device
        self.zh_model_path = zh_model_path
        self.en_model_path = en_model_path

        if self.verbose:
            print(
                "[lyric transcription] init: start:",
                f"device={device}",
                f"model_path={zh_model_path}",
            )

        # Always initialize Chinese ASR.
        self.zh_model = _ASRZhModel(device=device, model_path=zh_model_path)

        # English ASR will be lazily initialized on first English request to avoid long waiting cost when importing NeMo
        self.en_model = None

        if self.verbose:
            print("[lyric transcription] init: success")

    def process(self, wav_fn, language: str | None = "Mandarin", *, verbose: bool | None = None):
        """ Lyric transcriber process

        Args:
            wav_fn (str): Path to the audio file.
            language (str | None): Language of the audio. Defaults to "Mandarin". Supports "Mandarin", "Cantonese" and "English".
            verbose (bool | None): Whether to print verbose logs. Defaults to None.
        """
        v = self.verbose if verbose is None else verbose
        if language not in {"Mandarin", "Cantonese", "English"}:
            raise ValueError(f"Unsupported language: {language}, should be one of ['Mandarin', 'Cantonese', 'English']")
        if v:
            print(f"[lyric transcription] process: start: wav_fn={wav_fn} language={language}")
            t0 = time.time()

        lang = (language or "auto").lower()
        if lang in {"english"}:
            if self.en_model is None:
                # Lazy-load English ASR (Whisper on Apple Silicon, else NeMo) when first needed.
                if v:
                    hint = "Whisper" if _is_apple_silicon() else "NeMo"
                    print(f"[lyric transcription] init English ASR ({hint})")
                self.en_model = _ASREnModel(model_path=self.en_model_path, device=self.device)
            out = self.en_model.process(wav_fn)
        else:
            out = self.zh_model.process(wav_fn)

        if v:
            words, durs = out
            n_words = len(words) if isinstance(words, list) else 0
            dur_sum = float(sum(durs)) if isinstance(durs, list) else 0.0
            dt = time.time() - t0
            print(
                "[lyric transcription] process: done:",
                f"n_words={n_words}",
                f"dur_sum={dur_sum:.3f}s",
                f"time={dt:.3f}s",
            )

        return out


if __name__ == "__main__":
    m = LyricTranscriber(
        zh_model_path="pretrained_models/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        en_model_path="pretrained_models/parakeet-tdt-0.6b-v2/parakeet-tdt-0.6b-v2.nemo",
        device="mps"
    )
    print(m.process("example/test/asr_zh.wav", language="Mandarin"))
    print(m.process("example/test/asr_en.wav", language="English"))
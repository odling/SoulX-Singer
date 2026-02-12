"""
SoulX-Singer MIDI -> metadata converter (no WAV required).

Generates SoulX-Singer-style metadata JSON directly from MIDI files,
synthesizing f0 from MIDI pitches instead of extracting from audio.
"""
import json
import math
import os
from dataclasses import dataclass
from typing import List, Tuple

import mido

from .g2p import g2p_transform


# Segmenting constants
DEFAULT_LANGUAGE = "English"
MAX_GAP_SEC = 5.0  # gap (sec) above which we start a new segment
MAX_SEGMENT_DUR_SUM_SEC = 60.0  # max cumulative note duration per segment (sec)
MIN_GAP_THRESHOLD_SEC = 0.001  # ignore gaps smaller than this
LONG_SILENCE_THRESHOLD_SEC = 0.05  # treat as separate <SP> if gap larger
MAX_LEADING_SP_DUR_SEC = 2.0  # cap leading silence in a segment to this (sec)

# F0 synthesis constants
F0_FRAME_RATE_HZ = 50  # frames per second for f0 (20ms per frame)


@dataclass
class Note:
    """Single note with timing, text, pitch, and type."""
    start_s: float
    note_dur: float
    note_text: str
    note_pitch: int
    note_type: int

    @property
    def end_s(self) -> float:
        return self.start_s + self.note_dur


def midi_pitch_to_hz(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz."""
    if midi_note <= 0:
        return 0.0
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def synthesize_f0(notes: List[Note], total_duration_s: float) -> List[float]:
    """
    Synthesize frame-level f0 from note pitches.
    
    Args:
        notes: List of notes with timing and pitch info
        total_duration_s: Total duration in seconds
        
    Returns:
        List of f0 values at F0_FRAME_RATE_HZ
    """
    frame_duration = 1.0 / F0_FRAME_RATE_HZ
    num_frames = int(math.ceil(total_duration_s * F0_FRAME_RATE_HZ))
    f0_values = [0.0] * num_frames
    
    for note in notes:
        if note.note_type == 1 or note.note_pitch <= 0:  # Rest/silence
            continue
            
        hz = midi_pitch_to_hz(note.note_pitch)
        start_frame = int(note.start_s * F0_FRAME_RATE_HZ)
        end_frame = int(note.end_s * F0_FRAME_RATE_HZ)
        
        for frame_idx in range(max(0, start_frame), min(num_frames, end_frame)):
            f0_values[frame_idx] = hz
    
    return f0_values


def midi2notes(midi_path: str) -> List[Note]:
    """
    Parse MIDI file into a list of Note objects.
    
    Extracts notes and lyrics from MIDI, handling tempo, overlapping notes,
    and lyric-to-note alignment.
    """
    mid = mido.MidiFile(midi_path)
    ticks_per_beat = mid.ticks_per_beat
    tempo = 500000  # default: 120 BPM

    raw_notes: List[dict] = []
    lyrics: List[Tuple[int, str]] = []

    # Extract notes and lyrics from all tracks
    for track in mid.tracks:
        abs_ticks = 0
        active = {}
        for msg in track:
            abs_ticks += msg.time
            if msg.type == "set_tempo":
                tempo = msg.tempo
            elif msg.type == "lyrics":
                text = msg.text
                try:
                    text = text.encode("latin1").decode("utf-8")
                except Exception:
                    pass
                lyrics.append((abs_ticks, text))
            elif msg.type == "note_on":
                key = (msg.channel, msg.note)
                if msg.velocity > 0:
                    active[key] = (abs_ticks, msg.velocity)
                else:
                    if key in active:
                        start_ticks, vel = active.pop(key)
                        raw_notes.append({
                            "midi": msg.note,
                            "start_ticks": start_ticks,
                            "duration_ticks": abs_ticks - start_ticks,
                            "velocity": vel,
                            "lyric": "",
                        })
            elif msg.type == "note_off":
                key = (msg.channel, msg.note)
                if key in active:
                    start_ticks, vel = active.pop(key)
                    raw_notes.append({
                        "midi": msg.note,
                        "start_ticks": start_ticks,
                        "duration_ticks": abs_ticks - start_ticks,
                        "velocity": vel,
                        "lyric": "",
                    })

    if not raw_notes:
        raise ValueError("No notes found in MIDI file")

    # Compute end ticks and sort
    for n in raw_notes:
        n["end_ticks"] = n["start_ticks"] + n["duration_ticks"]
    raw_notes.sort(key=lambda n: n["start_ticks"])
    lyrics.sort(key=lambda x: x[0])

    # Trim overlapping notes
    trimmed = []
    for note in raw_notes:
        while trimmed:
            prev = trimmed[-1]
            if note["start_ticks"] < prev["end_ticks"]:
                prev["end_ticks"] = note["start_ticks"]
                prev["duration_ticks"] = prev["end_ticks"] - prev["start_ticks"]
                if prev["duration_ticks"] <= 0:
                    trimmed.pop()
                    continue
            break
        trimmed.append(note)
    raw_notes = trimmed

    # Match lyrics to notes
    tolerance = ticks_per_beat // 100
    lyric_idx = 0
    for note in raw_notes:
        while lyric_idx < len(lyrics) and lyrics[lyric_idx][0] < note["start_ticks"] - tolerance:
            lyric_idx += 1
        if lyric_idx < len(lyrics):
            lyric_ticks, lyric_text = lyrics[lyric_idx]
            if abs(lyric_ticks - note["start_ticks"]) <= tolerance:
                note["lyric"] = lyric_text
                lyric_idx += 1

    def ticks_to_seconds(ticks: int) -> float:
        return (ticks / ticks_per_beat) * (tempo / 1_000_000)

    # Convert to Note objects
    result: List[Note] = []
    prev_end_s = 0.0
    for idx, n in enumerate(raw_notes):
        start_s = ticks_to_seconds(n["start_ticks"])
        end_s = ticks_to_seconds(n["end_ticks"])
        if prev_end_s > start_s:
            start_s = prev_end_s
        dur_s = end_s - start_s
        if dur_s <= 0:
            continue

        lyric = n.get("lyric", "")
        if not lyric:
            tp = 2
            text = "la"  # default syllable for notes without lyrics
        elif lyric == "<SP>":
            tp = 1
            text = "<SP>"
        elif lyric == "-":
            tp = 3
            text = raw_notes[idx - 1].get("lyric", "-") if idx > 0 else "-"
        else:
            tp = 2
            text = lyric

        result.append(Note(
            start_s=start_s,
            note_dur=dur_s,
            note_text=text,
            note_pitch=n["midi"],
            note_type=tp,
        ))
        prev_end_s = end_s

    return result


def _new_segment() -> dict:
    """Create a fresh empty segment dict."""
    return {
        "note_text": [],
        "note_dur": [],
        "note_pitch": [],
        "note_type": [],
        "start_time_ms": 0,
        "end_time_ms": 0,
    }


def notes_to_segments(notes: List[Note]) -> List[dict]:
    """
    Convert a list of Notes into segments with proper gap handling.
    
    Returns a list of segment dicts with:
    - note_text, note_dur, note_pitch, note_type (as lists)
    - start_time_ms, end_time_ms
    """
    if not notes:
        return []
    
    segments = []
    current_segment = _new_segment()
    prev_end = 0.0
    dur_sum = 0.0
    
    for note in notes:
        gap = note.start_s - prev_end
        
        # Cap leading silence: if last entry is a long <SP>, trim and save segment
        if (
            current_segment["note_text"]
            and current_segment["note_text"][-1] == "<SP>"
            and current_segment["note_dur"][-1] > MAX_LEADING_SP_DUR_SEC
        ):
            current_segment["note_dur"][-1] = MAX_LEADING_SP_DUR_SEC
            # Update end_time_ms to reflect trimmed duration
            total_dur_ms = int(sum(current_segment["note_dur"]) * 1000)
            current_segment["end_time_ms"] = current_segment["start_time_ms"] + total_dur_ms
            segments.append(current_segment)
            current_segment = _new_segment()
            prev_end = note.start_s
            dur_sum = 0.0
            gap = 0.0
        
        # Check if we need to start a new segment
        if gap >= MAX_GAP_SEC or dur_sum >= MAX_SEGMENT_DUR_SUM_SEC:
            if current_segment["note_text"]:
                segments.append(current_segment)
                current_segment = _new_segment()
                dur_sum = 0.0
        
        # Handle gaps between notes
        if gap > MIN_GAP_THRESHOLD_SEC:
            if gap > LONG_SILENCE_THRESHOLD_SEC or not current_segment["note_text"]:
                # Insert <SP> for larger gaps or at segment start
                if not current_segment["note_text"]:
                    current_segment["start_time_ms"] = int(prev_end * 1000)
                current_segment["note_text"].append("<SP>")
                current_segment["note_dur"].append(gap)
                current_segment["note_pitch"].append(0)
                current_segment["note_type"].append(1)
            else:
                # Extend previous note's duration to fill small gaps
                if current_segment["note_dur"]:
                    current_segment["note_dur"][-1] += gap
        
        # Add the note
        if not current_segment["note_text"]:
            current_segment["start_time_ms"] = int(note.start_s * 1000)
        
        current_segment["note_text"].append(note.note_text)
        current_segment["note_dur"].append(note.note_dur)
        current_segment["note_pitch"].append(note.note_pitch)
        current_segment["note_type"].append(note.note_type)
        current_segment["end_time_ms"] = int(note.end_s * 1000)
        
        prev_end = note.end_s
        dur_sum += note.note_dur
    
    # Add final segment
    if current_segment["note_text"]:
        segments.append(current_segment)
    
    return segments


def merge_duplicate_notes(segment: dict) -> dict:
    """Merge consecutive identical notes (same text, pitch, type) within a segment."""
    texts = segment["note_text"]
    durs = segment["note_dur"]
    pitches = segment["note_pitch"]
    types = segment["note_type"]
    
    if not texts:
        return segment
    
    new_texts = [texts[0]]
    new_durs = [durs[0]]
    new_pitches = [pitches[0]]
    new_types = [types[0]]
    
    for i in range(1, len(texts)):
        t, d, p, ty = texts[i], durs[i], pitches[i], types[i]
        
        # Merge consecutive <SP>
        if t == "<SP>" and new_texts[-1] == "<SP>":
            new_durs[-1] += d
            continue
        
        # Merge identical notes
        if t == new_texts[-1] and p == new_pitches[-1] and ty == new_types[-1]:
            new_durs[-1] += d
        else:
            new_texts.append(t)
            new_durs.append(d)
            new_pitches.append(p)
            new_types.append(ty)
    
    return {
        "note_text": new_texts,
        "note_dur": new_durs,
        "note_pitch": new_pitches,
        "note_type": new_types,
        "start_time_ms": segment["start_time_ms"],
        "end_time_ms": segment["end_time_ms"],
    }


def segment_to_metadata(segment: dict, index: int, language: str) -> dict:
    """
    Convert a segment dict to final metadata format.
    
    Generates phonemes and synthesizes f0 from note pitches.
    """
    # Merge duplicates
    segment = merge_duplicate_notes(segment)
    
    texts = segment["note_text"]
    durs = segment["note_dur"]
    pitches = segment["note_pitch"]
    types = segment["note_type"]
    start_ms = segment["start_time_ms"]
    end_ms = segment["end_time_ms"]
    
    # Generate phonemes
    phonemes = g2p_transform(texts, language)
    
    # Create notes for f0 synthesis
    notes_for_f0 = []
    current_time = 0.0
    for text, dur, pitch, tp in zip(texts, durs, pitches, types):
        notes_for_f0.append(Note(
            start_s=current_time,
            note_dur=dur,
            note_text=text,
            note_pitch=pitch,
            note_type=tp,
        ))
        current_time += dur
    
    # Synthesize f0
    total_duration = sum(durs)
    f0_values = synthesize_f0(notes_for_f0, total_duration)
    
    # Build the item name
    item_name = f"vocal_{start_ms}_{end_ms}"
    
    return {
        "index": item_name,
        "language": language,
        "time": [start_ms, end_ms],
        "duration": " ".join(str(round(d, 2)) for d in durs),
        "text": " ".join(texts),
        "phoneme": " ".join(phonemes),
        "note_pitch": " ".join(str(p) for p in pitches),
        "note_type": " ".join(str(t) for t in types),
        "f0": " ".join(str(round(f, 1)) for f in f0_values),
    }


def midi2meta_pure(
    midi_path: str,
    output_path: str,
    language: str = DEFAULT_LANGUAGE,
) -> List[dict]:
    """
    Convert MIDI file to SoulX-Singer metadata JSON without requiring audio.
    
    Args:
        midi_path: Path to input MIDI file
        output_path: Path to output JSON file
        language: Language for phoneme conversion ("English", "Mandarin", "Cantonese")
        
    Returns:
        List of metadata segment dicts
    """
    # Parse MIDI to notes
    notes = midi2notes(midi_path)
    
    if not notes:
        raise ValueError("No notes extracted from MIDI")
    
    # Convert to segments
    segments = notes_to_segments(notes)
    
    # Convert each segment to metadata format
    metadata = []
    for idx, segment in enumerate(segments):
        meta_item = segment_to_metadata(segment, idx, language)
        metadata.append(meta_item)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"Saved metadata to {output_path}")
    print(f"  - {len(metadata)} segment(s)")
    print(f"  - {sum(len(s['text'].split()) for s in metadata)} total notes")
    
    return metadata


def create_metadata_from_notes(
    notes_data: List[dict],
    output_path: str,
    language: str = DEFAULT_LANGUAGE,
) -> List[dict]:
    """
    Create metadata from a list of note dictionaries.
    
    Useful for programmatic metadata generation without MIDI.
    
    Args:
        notes_data: List of dicts with keys: start, end, text, pitch, type
        output_path: Path to output JSON file
        language: Language for phoneme conversion
        
    Returns:
        List of metadata segment dicts
    """
    notes = [
        Note(
            start_s=n["start"],
            note_dur=n["end"] - n["start"],
            note_text=n["text"],
            note_pitch=n["pitch"],
            note_type=n.get("type", 2),
        )
        for n in notes_data
    ]
    
    # Convert to segments
    segments = notes_to_segments(notes)
    
    # Convert each segment to metadata format
    metadata = []
    for idx, segment in enumerate(segments):
        meta_item = segment_to_metadata(segment, idx, language)
        metadata.append(meta_item)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"Saved metadata to {output_path}")
    
    return metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert MIDI to SoulX-Singer metadata JSON (no WAV required)."
    )
    parser.add_argument(
        "--midi",
        type=str,
        required=True,
        help="Path to input MIDI file",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output JSON file",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=DEFAULT_LANGUAGE,
        choices=["English", "Mandarin", "Cantonese"],
        help="Language for phoneme conversion (default: English)",
    )
    
    args = parser.parse_args()
    
    midi2meta_pure(
        midi_path=args.midi,
        output_path=args.output,
        language=args.language,
    )

"""
Convert downloaded English metadata (word + phone annotations) from the
SoulX-Singer-Eval-Dataset into the target metadata format expected by SoulX-Singer.

Target format per entry (wrapped in a JSON list):
{
  "index": "...",
  "language": "English",
  "time": [0, total_ms],
  "duration": "dur1 dur2 ...",          (space-separated, per word/note)
  "text": "<SP> word1 word2 ... <SP>",  (space-separated)
  "phoneme": "<SP> en_PH1-PH2 ... <SP>",(space-separated, phonemes grouped per word)
  "note_pitch": "0 60 62 ... 0",        (space-separated)
  "note_type": "1 2 2 ... 1",           (space-separated)
  "f0": "0.0 0.0 246.9 ..."             (space-separated, 50 Hz sample rate)
}
"""

import os
import json
import math
import glob

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_DIR = os.path.join(BASE_DIR, "example-metadata")
OUTPUT_DIR = os.path.join(BASE_DIR, "example-metadata-target")
F0_SAMPLE_RATE = 50.0  # Hz  (20 ms per frame)

# Source datasets to pair (word, phone)
DATASET_PAIRS = [
    # (word_subdir, phone_subdir)
    ("soulxsinger_eval.word.target", "soulxsinger_eval.phone.target"),
    ("soulxsinger_eval.word.prompt", "soulxsinger_eval.phone.prompt"),
    ("opensource_eval.word.target", "opensource_eval.phone.target"),
    ("opensource_eval.word.prompt", "opensource_eval.phone.prompt"),
]


# ---------------------------------------------------------------------------
# Utility: MIDI -> Hz
# ---------------------------------------------------------------------------
def midi_to_hz(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz."""
    return 440.0 * (2 ** ((midi_note - 69) / 12))


# ---------------------------------------------------------------------------
# F0 contour generation (simplified from metadata_generator.py)
# ---------------------------------------------------------------------------
def generate_f0_contour(note_pitches, durations, note_types=None,
                        phonemes=None, sample_rate=F0_SAMPLE_RATE):
    """
    Generate an F0 contour from note-level pitches and durations.
    Adds light vibrato for voiced segments and word-boundary silence.
    """
    f0 = []
    cumulative = 0.0
    vibrato_depth = 5.0  # Hz
    vibrato_rate = 5.5   # Hz

    for i, (pitch, dur) in enumerate(zip(note_pitches, durations)):
        cumulative += dur
        target_total = round(cumulative * sample_rate)
        n_samples = max(1, target_total - len(f0))

        if pitch == 0:
            f0.extend([0.0] * n_samples)
            continue

        # Word-boundary onset/offset silence frames
        nt = note_types[i] if note_types and i < len(note_types) else 2
        onset = 2 if nt == 2 else 0
        offset = 2 if nt == 2 else 0

        # Don't let silence exceed 40% of frames
        max_sil = n_samples * 2 // 5
        if onset + offset > max_sil:
            scale = max_sil / (onset + offset)
            onset = int(onset * scale)
            offset = int(offset * scale)

        voiced = max(1, n_samples - onset - offset)

        f0.extend([0.0] * onset)

        base_f0 = midi_to_hz(pitch)
        for s in range(voiced):
            t = s / max(1, voiced - 1) if voiced > 1 else 0.0
            vib = vibrato_depth * math.sin(2 * math.pi * vibrato_rate * t)
            val = base_f0 + vib

            # Portamento to next pitched note
            if i < len(note_pitches) - 1 and note_pitches[i + 1] != 0 and t > 0.7:
                next_f0 = midi_to_hz(note_pitches[i + 1])
                slide = (t - 0.7) / 0.3
                val = base_f0 + (next_f0 - base_f0) * slide
            f0.append(round(val, 1))

        f0.extend([0.0] * offset)

    return f0


# ---------------------------------------------------------------------------
# Group phonemes by word using cumulative duration alignment
# ---------------------------------------------------------------------------
def group_phonemes_by_word(word_texts, word_durs, phonemes, ph_durs, tolerance=0.02):
    """
    Align phone-level phonemes to word-level notes using cumulative durations.
    Returns a list of phoneme-group strings, one per word entry.
    """
    # Build cumulative durations for words
    word_cum = []
    acc = 0.0
    for d in word_durs:
        acc += d
        word_cum.append(round(acc, 6))

    # Walk through phonemes, accumulating into current word
    ph_groups = []
    current_phs = []
    ph_acc = 0.0
    word_idx = 0

    for ph, pd in zip(phonemes, ph_durs):
        ph_acc += pd
        current_phs.append(ph)

        # Check if we've reached the end of the current word
        if word_idx < len(word_cum) and ph_acc >= word_cum[word_idx] - tolerance:
            # Format the phoneme group
            word = word_texts[word_idx] if word_idx < len(word_texts) else ""
            ph_groups.append(format_phoneme_group(current_phs, word))
            current_phs = []
            word_idx += 1

    # Handle any remaining phonemes
    if current_phs:
        word = word_texts[word_idx] if word_idx < len(word_texts) else ""
        ph_groups.append(format_phoneme_group(current_phs, word))
        word_idx += 1

    # If we have fewer groups than words (duration rounding), pad with the word text
    while len(ph_groups) < len(word_texts):
        w = word_texts[len(ph_groups)]
        if w in ("<SP>", "<AP>"):
            ph_groups.append(w)
        else:
            ph_groups.append(f"en_{w.upper()}")
        word_idx += 1

    return ph_groups


def format_phoneme_group(phs, word_text):
    """Format a list of phonemes into the target phoneme string for one word."""
    # Filter out empty strings
    phs = [p for p in phs if p]

    if not phs:
        return "<SP>"

    # If the group is a single special token
    if len(phs) == 1 and phs[0] in ("<SP>", "<AP>"):
        return phs[0]

    # If the word itself is a special token, keep it
    if word_text in ("<SP>", "<AP>"):
        return word_text

    # Join phonemes with dash, prefix with en_
    return "en_" + "-".join(phs)


# ---------------------------------------------------------------------------
# Convert a single item
# ---------------------------------------------------------------------------
def convert_item(word_data, phone_data):
    """
    Convert a word-level + phone-level annotation pair into
    the SoulX-Singer target metadata format.
    """
    item_name = word_data["item_name"]
    note_text = word_data["note_text"]
    note_dur = word_data["note_dur"]
    note_pitch = word_data["note_pitch"]
    note_type = word_data["note_type"]

    phonemes = phone_data["ph"]
    ph_durs = phone_data["ph_durs"]

    # Group phonemes by word
    ph_groups = group_phonemes_by_word(note_text, note_dur, phonemes, ph_durs)

    # Generate F0 contour
    f0_contour = generate_f0_contour(note_pitch, note_dur, note_type, ph_groups)

    # Compute time from F0 length (20ms per frame at 50 Hz)
    time_ms = len(f0_contour) * 20

    # Build the target metadata entry
    metadata = {
        "index": item_name,
        "language": "English",
        "time": [0, time_ms],
        "duration": " ".join(f"{d:.2f}" for d in note_dur),
        "text": " ".join(note_text),
        "phoneme": " ".join(ph_groups),
        "note_pitch": " ".join(str(p) for p in note_pitch),
        "note_type": " ".join(str(t) for t in note_type),
        "f0": " ".join(f"{f:.1f}" for f in f0_contour),
    }

    return metadata


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_converted = 0
    total_skipped = 0

    for word_subdir, phone_subdir in DATASET_PAIRS:
        word_dir = os.path.join(METADATA_DIR, word_subdir)
        phone_dir = os.path.join(METADATA_DIR, phone_subdir)

        if not os.path.isdir(word_dir) or not os.path.isdir(phone_dir):
            print(f"Skipping pair ({word_subdir}, {phone_subdir}) — directory not found")
            continue

        # Determine output sub-folder name (use the word subdir name without word/phone)
        # e.g. "opensource_eval.word.target" -> "opensource_eval.target"
        out_name = word_subdir.replace(".word.", ".")
        out_dir = os.path.join(OUTPUT_DIR, out_name)
        os.makedirs(out_dir, exist_ok=True)

        # Build index of phone-level files
        phone_files = {}
        for fp in glob.glob(os.path.join(phone_dir, "*.json")):
            with open(fp) as f:
                data = json.load(f)
            phone_files[data["item_name"]] = data

        # Process word-level files
        pair_converted = 0
        pair_skipped = 0

        for fp in sorted(glob.glob(os.path.join(word_dir, "*.json"))):
            with open(fp) as f:
                word_data = json.load(f)

            item_name = word_data["item_name"]

            if item_name not in phone_files:
                pair_skipped += 1
                continue

            phone_data = phone_files[item_name]

            try:
                metadata = convert_item(word_data, phone_data)
            except Exception as e:
                print(f"  ERROR converting {item_name}: {e}")
                pair_skipped += 1
                continue

            # Save as [metadata] (list wrapping, matching existing format)
            safe_name = item_name.replace("/", "_").replace("\\", "_")
            out_path = os.path.join(out_dir, f"{safe_name}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([metadata], f, indent=2, ensure_ascii=False)

            pair_converted += 1

        print(f"{word_subdir} + {phone_subdir}: "
              f"converted {pair_converted}, skipped {pair_skipped}")
        total_converted += pair_converted
        total_skipped += pair_skipped

    print(f"\n{'='*60}")
    print(f"Done! Converted {total_converted} files to target format.")
    if total_skipped:
        print(f"Skipped {total_skipped} files (missing phone-level pair or errors).")
    print(f"Output directory: {OUTPUT_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

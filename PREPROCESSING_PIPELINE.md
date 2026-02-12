# SoulX-Singer Preprocessing Pipeline Analysis

## Overview

This document describes the step-by-step workflow for converting raw MIDI data (from a DAW like Ableton) into SoulX-Singer metadata JSON, which is the format the singing voice synthesis model consumes. The pipeline has two paths:

- **Original path** (`midi_parser.py`): Requires a WAV vocal file alongside the MIDI
- **Pure path** (`midi_parser_pure.py`): Works with MIDI only, no audio needed

---

## Pipeline Diagram

```
                     ┌──────────────────┐
                     │  Ableton / DAW   │
                     │  (compose notes) │
                     └────────┬─────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │   ableton-midi.mid  │
                   │  (notes + timing,   │
                   │   NO lyrics)        │
                   └────────┬────────────┘
                            │
                            ▼
              ┌──────────────────────────────┐
              │      MIDI Editor (Web App)   │
              │  - Add lyrics to each note   │
              │  - Adjust pitch / timing     │
              │  - Fix overlaps              │
              │  - Preview with audio        │
              └────────────┬─────────────────┘
                           │  Export
                           ▼
                  ┌──────────────────┐
                  │  vocal-midi.mid  │
                  │ (notes + lyrics) │
                  └───────┬──────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
    ┌─────────────────┐    ┌─────────────────────┐
    │  midi_parser.py │    │ midi_parser_pure.py  │
    │ (needs WAV)     │    │ (no WAV needed)      │
    └────────┬────────┘    └──────────┬───────────┘
             │                        │
             ▼                        ▼
       ┌──────────────────────────────────┐
       │       edit_metadata.json         │
       │  (SoulX-Singer training format)  │
       └──────────────────────────────────┘
```

---

## Step-by-Step Workflow

### Step 1: Compose Notes in a DAW (Ableton)

**What happens**: The user creates MIDI notes in Ableton (or any DAW) that represent the melody of the song. Each note has a pitch (which piano key), a start time, and a duration.

**Output**: `ableton-midi.mid` -- a standard MIDI file containing note-on/note-off events with pitch and timing information.

**What's missing**: This file has **no lyrics**. The MIDI standard supports lyric events, but DAWs typically don't add them. The notes only say "play this pitch for this long", not "sing this word".

---

### Step 2: Open the MIDI in the MIDI Editor

**What happens**: The user launches the MIDI Editor, a web application built with React. They click "Import MIDI" and load `ableton-midi.mid`.

**How it works internally**:
1. The editor uses the `@tonejs/midi` library to parse the binary MIDI file
2. It reads the tempo (BPM), time signature, and ticks-per-beat (PPQ) from the MIDI header
3. It extracts every note: MIDI pitch number, start time (in beats), duration (in beats), and velocity
4. It checks for any existing lyric meta-events in the MIDI and matches them to notes by tick position
5. All notes are loaded into a Zustand state store and displayed on a piano roll

**Key detail**: The editor preserves the original PPQ value so that when exporting, the timing precision matches the original file exactly.

---

### Step 3: Add Lyrics to Notes

**What happens**: The user assigns lyrics (text) to each note. There are two ways:

1. **Individual editing**: Click on a note in the lyric table on the right side panel and type the word/syllable for that note
2. **Bulk fill**: Paste or type full lyrics into the text area and press Enter. The editor uses a smart tokenizer that splits CJK characters one-per-note and English words one-per-note, then assigns them sequentially starting from the currently selected note

**Example**: If the lyrics are "you can do every day", and there are 5 notes selected, each note gets one word: "you", "can", "do", "every", "day".

**What this adds**: Each note now has a `lyric` field (e.g., `"you"`, `"can"`, `"啦"`) in addition to its pitch and timing.

---

### Step 4: Adjust Pitch and Timing (Optional)

**What happens**: The user fine-tunes note properties using the piano roll or the lyric table:

- **Move notes**: Drag notes on the piano roll to change their start time and pitch
- **Resize notes**: Drag the left/right edges of a note to change its start or duration
- **Edit values directly**: In the lyric table, click on PITCH, START, or END cells to type exact values (seconds for timing, MIDI number for pitch)
- **Keyboard shortcuts**: Cmd/Ctrl + Up/Down arrow to adjust pitch by one semitone
- **Transpose**: Shift all notes up or down by a fixed number of semitones using the transpose dropdown

**Snapping**: Note positions snap to a grid. The snap resolution gets finer as you zoom in (0.1s at 1x zoom down to 0.01s at 8x zoom).

---

### Step 5: Load Reference Audio (Optional)

**What happens**: The user can import a WAV/MP3 audio file to see the waveform alongside the piano roll. This helps align notes to the actual singing.

**How it works**:
- The audio is displayed as a waveform using WaveSurfer.js above the piano roll
- Both views scroll together horizontally
- The user can play back the audio and MIDI synth simultaneously, with independent volume controls
- The audio is only for visual/auditory reference -- it is **not** embedded into the MIDI

---

### Step 6: Fix Overlapping Notes

**What happens**: The user clicks "Fix Overlaps" (or it happens automatically on export). The editor scans all notes sorted by start time and, for any pair where note A's end time exceeds note B's start time, trims note A so it ends exactly where note B begins.

**Why this matters**: Overlapping notes cause problems downstream because the parser expects notes to be sequential with clear boundaries. The SoulX-Singer model assumes one syllable sounds at a time.

---

### Step 7: Export the Edited MIDI

**What happens**: The user clicks "Export MIDI". The editor generates a new MIDI file (`vocal-midi.mid`) that contains:

1. A **set_tempo** meta event (BPM converted to microseconds-per-beat)
2. A **time_signature** meta event
3. For each note:
   - A **lyrics** meta event at the note's start tick (the lyric text, UTF-8 encoded as Latin-1 bytes for MIDI compatibility)
   - A **note_on** event at the start tick
   - A **note_off** event at the end tick
4. An **end_of_track** meta event

**Event ordering**: At the same tick position, events are ordered: note_off first, then lyrics, then note_on. This ensures clean transitions between notes.

**Encoding**: Non-ASCII lyrics (Chinese characters, etc.) are encoded as UTF-8 byte sequences stored as Latin-1 characters in the MIDI file. The parser reverses this encoding when reading.

---

### Step 8: Parse the MIDI into Notes (Both Parsers)

**What happens**: The MIDI file `vocal-midi.mid` is parsed back into an internal list of `Note` objects.

**How it works (identical in both parsers)**:
1. Read all tracks from the MIDI file
2. Track absolute tick position for each event
3. Capture the last `set_tempo` event to know the tempo
4. Collect all `lyrics` events with their tick positions
5. Collect all `note_on`/`note_off` pairs to build raw notes (pitch, start tick, duration ticks)
6. Sort notes by start tick
7. **Trim overlapping notes**: If a note overlaps with the next one, the earlier note is shortened so it ends where the next one begins. If trimming makes a note zero-length, it's removed entirely
8. **Match lyrics to notes**: Using a tolerance of `ticks_per_beat / 100`, find the lyric event closest to each note's start tick and assign it. The Latin-1 → UTF-8 decode is applied here
9. **Convert ticks to seconds**: Using `(ticks / ticks_per_beat) * (tempo / 1,000,000)`
10. **Determine note type**:
    - No lyric → type `2` (sung note), text defaults to `"la"` / `"啦"`
    - Lyric is `"<SP>"` → type `1` (silence/rest)
    - Lyric is `"-"` → type `3` (continuation/melisma, inherits text from previous note)
    - Otherwise → type `2` (normal sung note)

**Output**: A list of `Note` objects, each with: `start_s` (seconds), `note_dur` (seconds), `note_text`, `note_pitch` (MIDI number), `note_type` (1/2/3).

---

### Step 9a: Segment, Cut WAV, and Extract F0 (Original Parser)

**What happens** (`midi_parser.py`): Notes are grouped into segments, audio is sliced, and real F0 is extracted from the audio.

**Detailed sub-steps**:

1. **Load the vocal WAV file** using librosa at 44100 Hz sample rate

2. **Iterate through notes** and group them into segments based on these rules:
   - Start a **new segment** if the gap from the previous note exceeds **5 seconds**
   - Start a **new segment** if the cumulative note duration exceeds **60 seconds**
   - If the leading silence (`<SP>`) in a segment exceeds **2 seconds**, split at that point

3. **Handle gaps between notes**:
   - Gaps smaller than **0.001 seconds** are ignored (considered rounding errors)
   - Gaps between **0.001 and 0.05 seconds**: the previous note is extended to fill the gap (no silence marker added)
   - Gaps larger than **0.05 seconds**: a `<SP>` (silence) note is inserted

4. **Cut WAV segments**: For each segment, slice the audio from the first note's start to the last note's end, and save it as a separate WAV file in a temporary directory

5. **Merge consecutive duplicates**: Within each segment, merge consecutive notes that have the same text, pitch, and type (their durations are summed). Consecutive `<SP>` entries are also merged

6. **Extract F0 using RMVPE**: For each cut WAV segment:
   - Load audio at 16kHz
   - Run through the RMVPE neural network (a deep learning pitch detector)
   - Interpolate the raw F0 to the target sample rate grid
   - The result is a sequence of frequency values (Hz), with `0.0` for unvoiced frames

7. **Generate phonemes**: Run each note's text through the G2P (grapheme-to-phoneme) converter, which supports English, Mandarin, and Cantonese

8. **Build final metadata**: Assemble the JSON with all fields

9. **Clean up**: Delete the temporary WAV directory

---

### Step 9b: Segment and Synthesize F0 (Pure Parser)

**What happens** (`midi_parser_pure.py`): Notes are grouped into segments and F0 is synthesized mathematically from MIDI pitches.

**Detailed sub-steps**:

1. **Iterate through notes** and group into segments:
   - Start a **new segment** if the gap exceeds **5 seconds**
   - Start a **new segment** if cumulative duration exceeds **60 seconds**
   - Gaps larger than **0.05 seconds**: insert a `<SP>` silence note

2. **Merge consecutive duplicates**: Same logic as the original parser

3. **Synthesize F0**: For each segment, convert MIDI pitch numbers to frequencies using the formula:
   ```
   frequency = 440.0 * 2^((midi_note - 69) / 12)
   ```
   Then fill a frame-level F0 array (50 frames per second = 20ms per frame):
   - For each note, set all frames within its time range to the computed frequency
   - Rest notes (type 1) and pitch 0 produce `0.0` (silence)

4. **Generate phonemes**: Same G2P conversion as the original parser

5. **Build final metadata**: Same JSON structure

---

### Step 10: Output -- `edit_metadata.json`

**What the file contains**: A JSON array where each element is one segment with these fields:

| Field | Description | Example |
|-------|-------------|---------|
| `index` | Unique segment identifier | `"vocal_0_18229"` |
| `language` | Language for G2P | `"English"` |
| `time` | `[start_ms, end_ms]` of the segment | `[0, 18229]` |
| `duration` | Space-separated note durations in seconds | `"0.74 0.11 0.15 ..."` |
| `text` | Space-separated note texts | `"<SP> you can <SP> do ..."` |
| `phoneme` | Space-separated phoneme representations | `"<SP> en_Y-UW1 en_K-AE1-N ..."` |
| `note_pitch` | Space-separated MIDI pitch numbers | `"0 53 53 0 53 55 ..."` |
| `note_type` | Space-separated note types (1=rest, 2=sung, 3=continuation) | `"1 2 2 1 2 2 ..."` |
| `f0` | Space-separated frame-level F0 values in Hz | `"0.0 0.0 ... 174.6 174.6 ..."` |

---

## Full Preprocessing Pipeline (Automated - `pipeline.py`)

For reference, the automated pipeline (which is separate from the manual MIDI editing flow) does the following:

1. **Vocal Separation**: Split the full mix into vocals and accompaniment using a mel-band RoFormer model, then de-reverb the vocals
2. **F0 Extraction**: Extract pitch contour from the clean vocal using RMVPE
3. **Vocal Detection**: Find segments where singing occurs (based on voiced frames in F0)
4. **Per-segment F0**: Extract F0 for each cut segment
5. **Lyric Transcription**: Run ASR (Chinese: SeACo-Paraformer; English: Whisper/NeMo) to get word-level timestamps
6. **Note Transcription**: Run ROSVOT model to detect note boundaries and pitches
7. **Segment Merging**: Merge short segments into longer ones (up to 60s)
8. **Final F0**: Re-extract F0 for merged segments
9. **Output**: Write `metadata.json`

---

## Detailed Comparison: `midi_parser.py` vs `midi_parser_pure.py`

### Architecture

| Aspect | `midi_parser.py` (Original) | `midi_parser_pure.py` (Pure) |
|--------|----------------------------|------------------------------|
| **Dependencies** | `mido`, `librosa`, `soundfile`, `torch` (RMVPE model) | `mido` only (+ `g2p` for phonemes) |
| **Requires WAV** | Yes -- vocal audio file is mandatory | No -- works from MIDI alone |
| **Requires GPU/Model** | Yes -- RMVPE model weights (~80MB) | No |
| **Lines of code** | 669 | 506 |
| **Bidirectional** | Yes -- supports meta→MIDI and MIDI→meta | One-way -- MIDI→meta only |

### F0 Generation -- The Core Difference

**Original (`midi_parser.py`)**:
- Loads the vocal WAV file segment
- Runs it through RMVPE (a neural network trained on singing voice)
- Produces **real F0** that captures vibrato, pitch bending, slides between notes, natural intonation variations, and unvoiced consonants
- Frame rate determined by RMVPE internals (160 samples at 16kHz = 10ms hop, then interpolated)
- Example: a note at MIDI 64 (E4, ~329.6 Hz) might produce F0 values like `318.9 332.2 331.2 323.9 312.3` -- showing natural pitch fluctuation

**Pure (`midi_parser_pure.py`)**:
- Converts MIDI note number to Hz using the formula: `440 * 2^((note-69)/12)`
- Produces **perfectly flat F0** -- each note is a constant frequency with no variation
- Frame rate: 50 Hz (20ms per frame), hardcoded
- Example: the same MIDI 64 note produces `329.6 329.6 329.6 329.6 329.6` -- perfectly quantized

**Impact**: The synthesized F0 lacks the expressiveness of real singing. If the downstream model was trained on real F0 data (with vibrato and pitch drift), feeding it perfectly flat F0 may cause it to generate unnatural-sounding output. However, for scenarios where expressiveness comes from the model itself rather than the input F0, this may be acceptable.

### Segmentation Logic

**Original (`midi_parser.py`)**:

Uses `_edit_data_to_meta()` with these behaviors:
- Three thresholds for gaps:
  - `MIN_GAP_THRESHOLD_SEC = 0.001` -- gaps below this are ignored entirely
  - `LONG_SILENCE_THRESHOLD_SEC = 0.05` -- gaps above this create a `<SP>` entry
  - Between 0.001 and 0.05 -- the previous note is **extended** to fill the gap (its duration grows)
- `MAX_LEADING_SP_DUR_SEC = 2.0` -- if a segment starts with a silence longer than 2 seconds, it's split: the current segment is saved and a new one begins with at most 2s of leading silence
- Segments are split when:
  - Gap from previous note >= 5 seconds
  - Gap from last note in current segment >= 5 seconds (double check)
  - Cumulative duration >= 60 seconds

**Pure (`midi_parser_pure.py`)**:

Uses `notes_to_segments()` with simpler logic:
- Only one threshold: `LONG_SILENCE_THRESHOLD_SEC = 0.05` -- any gap above this creates a `<SP>`
- **No small-gap extension** -- gaps between 0.001 and 0.05 seconds that would be handled by extending the previous note in the original are instead silently ignored (the gap disappears with no `<SP>` and no duration extension)
- **No leading silence cap** -- segments can start with arbitrarily long silences
- Segments are split when:
  - Gap >= 5 seconds
  - Cumulative duration >= 60 seconds

### Gap Handling Differences (Potential Issue)

| Gap Size | Original Behavior | Pure Behavior |
|----------|-------------------|---------------|
| < 0.001s | Ignored | Falls through to regular note addition (gap is implicitly lost) |
| 0.001s - 0.05s | Previous note's duration extended to fill gap | Gap is silently dropped (no `<SP>`, no extension) |
| 0.05s - 5.0s | `<SP>` inserted | `<SP>` inserted |
| > 5.0s | New segment started | New segment started |

**Problem area**: In the pure parser, gaps between 0.001s and 0.05s are effectively lost. The total duration of the segment's notes will not add up to the segment's actual time span. This could cause a subtle timing drift where notes don't perfectly cover the time range declared in the segment's `time` field.

### Leading Silence Handling (Potential Issue)

The original parser has a mechanism to prevent segments from starting with very long silences (> 2 seconds). When this happens, it saves the current segment and starts fresh. The pure parser lacks this, which means:

- A segment could have a 10-second leading silence followed by a short phrase
- This wastes compute during training (the model processes all those silence frames)
- The `time` field will show a very early start time even though actual content starts much later

### Default Language

| | Original | Pure |
|--|----------|------|
| Default | `"Mandarin"` | `"English"` |

This affects phoneme generation. If you forget to set the language parameter, the original generates Mandarin phonemes (e.g., `zh_ni3`) and the pure generates English phonemes (e.g., `en_Y-UW1`). Make sure to always pass the correct language explicitly.

### Default Syllable for Notes Without Lyrics

| | Original | Pure |
|--|----------|------|
| Default text | `"啦"` (Chinese character) | `"la"` (English) |

When a MIDI note has no lyric event attached, the parsers assign a default syllable. The original uses a Chinese character which generates a Mandarin phoneme, while the pure uses an English word. This could cause issues if the model expects consistent language within a segment.

### Segment Naming Convention

| | Original | Pure |
|--|----------|------|
| Pattern | `{base_filename}_{segment_index}` | `vocal_{start_ms}_{end_ms}` |
| Example | `edit_metadata_0` | `vocal_0_18229` |

The pure parser's naming is more descriptive (you can tell the time range from the name), but neither format matters for model training -- it's just an identifier.

### Metadata Fields Differences

| Field | Original | Pure |
|-------|----------|------|
| `wav_fn` | Present (path to cut WAV) | Absent |
| `origin_wav_fn` | Present (path to full vocal) | Absent |
| `item_name` | Present | Absent (uses `index` directly) |
| `start_time_ms` | Intermediate field | Intermediate field |
| `end_time_ms` | Intermediate field | Intermediate field |

The final JSON output format is the same for both parsers -- only the intermediate data structures differ.

### Duplicate Merging

| | Original | Pure |
|--|----------|------|
| Function | `remove_duplicate_segments()` | `merge_duplicate_notes()` |
| Approach | Mutates the segment list in-place | Returns a new segment dict |
| Logic | Identical | Identical |

Both merge consecutive notes with the same text, pitch, and type, and merge consecutive `<SP>` entries. The logic is functionally equivalent.

### Conversion Features

| Feature | Original | Pure |
|---------|----------|------|
| MIDI → Metadata | Yes | Yes |
| Metadata → MIDI | Yes (`meta2midi`) | No |
| Metadata → Notes | Yes (`meta2notes`) | No |
| Notes → MIDI | Yes (`notes2midi`) | No |
| Notes from dicts | No | Yes (`create_metadata_from_notes`) |

The original parser is fully bidirectional, which is useful for round-tripping (e.g., editing metadata and converting back to MIDI). The pure parser is one-directional but offers a convenient `create_metadata_from_notes()` API for programmatic note generation.

---

## Potential Issues and Areas of Improvement for the Pure Parser

### 1. Missing Small-Gap Duration Extension (Bug Risk)

**Problem**: Gaps between 0.001s and 0.05s are silently dropped, causing a timing discrepancy between the sum of note durations and the segment's declared time range.

**Fix**: Add the same small-gap extension logic from the original:

```python
# In notes_to_segments(), after checking for long gaps:
elif gap > 0.001:  # Small gap - extend previous note
    if current_segment["note_dur"]:
        current_segment["note_dur"][-1] += gap
```

### 2. No Leading Silence Cap

**Problem**: Segments can start with arbitrarily long silences, wasting model compute.

**Fix**: Add a `MAX_LEADING_SP_DUR_SEC` constant and split segments when leading silence exceeds it, mirroring the original's behavior.

### 3. F0 Frame Rate Mismatch

**Problem**: The pure parser uses 50 Hz (20ms frames), but the actual downstream model may expect a different frame rate. The original parser's F0 frame rate is determined by the RMVPE model's configuration (typically 10ms hop at 16kHz, then interpolated to the target sample rate's hop size). If the model expects a specific frame rate, the pure parser's 50 Hz assumption may be wrong.

**Fix**: Make `F0_FRAME_RATE_HZ` configurable or match it to the model's expected hop size. Check what frame rate the training pipeline expects and use that.

### 4. Flat F0 May Reduce Model Quality

**Problem**: Perfectly quantized F0 (no vibrato, no pitch slides) may not match what the model was trained on. Real singing F0 has natural variation that the model may rely on.

**Possible improvements**:
- Add synthetic vibrato: a small sinusoidal modulation (e.g., +/- 20 cents at 5-6 Hz) on top of the base frequency
- Add pitch transitions: linear interpolation between consecutive notes of different pitches, covering the last ~50ms of the outgoing note and the first ~50ms of the incoming note
- Add slight random jitter: small random deviations (+/- 5 cents) to make the F0 less robotic

### 5. Hardcoded Language Default

**Problem**: The pure parser defaults to `"English"` while the rest of the codebase (automated pipeline, original parser) defaults to `"Mandarin"`.

**Fix**: Ensure consistent defaults or require the language parameter explicitly.

### 6. No `<AP>` Handling

**Problem**: The original parser's `meta2notes` function converts `<AP>` (aspiration pause) markers to `<SP>`. The pure parser does not handle `<AP>` at all since it only reads from MIDI (which only contains `<SP>` markers). This is not a current issue but could become one if the MIDI editor starts supporting `<AP>` markers.

### 7. No Validation of F0 Length vs Duration

**Problem**: The synthesized F0 length is computed as `ceil(total_duration * 50)`, but small floating-point rounding differences in note durations could cause the F0 array to be slightly longer or shorter than what the model expects for the declared duration. The original parser avoids this because RMVPE processes the actual audio and produces a deterministic number of frames.

**Fix**: After synthesis, verify that `len(f0) == expected_frames` based on the segment's total duration, and pad/trim if needed.

---

## Summary

The pure parser successfully eliminates the need for audio files, GPU access, and the RMVPE model. It produces structurally identical metadata JSON. The main tradeoffs are:

1. **F0 quality**: Synthesized (flat) vs extracted (expressive) -- this is the biggest quality impact
2. **Gap handling**: Slightly different behavior for very small gaps -- this is a bug that should be fixed
3. **Leading silence**: No cap in the pure parser -- minor issue, should be added
4. **Frame rate**: Hardcoded 50 Hz may not match model expectations -- should be verified

For use cases where the goal is to generate training data from scratch (no existing vocal recording), the pure parser is the right choice. The flat F0 concern can be mitigated by adding synthetic expressiveness or by training/fine-tuning the model on pure-parser output.

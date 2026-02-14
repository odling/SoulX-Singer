#!/usr/bin/env python3
"""
SoulX-Singer Metadata Generator
Generate vocal metadata with different styles: robotic, singing, speech, rap
"""

import json
import math
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass


# ============================================================================
# CMU PHONEME DICTIONARY (Simplified - add more words as needed)
# ============================================================================

CMU_DICT = {
    "you": "en_Y-UW1",
    "can": "en_K-AE1-N",
    "do": "en_D-UW1",
    "it": "en_IH1-T",
    "every": "en_EH1-V-ER0-IY0",
    "day": "en_D-EY1",
    "be": "en_B-IY1",
    "obsessed": "en_AH0-B-S-EH1-S-T",
    "a": "en_AH0",
    "little": "en_L-IH1-T-AH0-L",
    "bit": "en_B-IH1-T",
    "weird": "en_W-IH1-R-D",
    "but": "en_B-AH1-T",
    "actually": "en_AE1-K-CH-UW0-AH0-L-IY0",
    "powerful": "en_P-AW1-ER0-F-AH0-L",
    "how": "en_HH-AW1",
    "about": "en_AH0-B-AW1-T",
    "that": "en_DH-AE1-T",
    "who": "en_HH-UW1",
    "says": "en_S-EH1-Z",
    "you're": "en_Y-UH1-R",
    "not": "en_N-AA1-T",
    "pretty": "en_P-R-IH1-T-IY0",
    "beautiful": "en_B-Y-UW1-T-AH0-F-AH0-L",
    "the": "en_DH-AH0",
    "night": "en_N-AY1-T",
    "love": "en_L-AH1-V",
    "feel": "en_F-IY1-L",
    "this": "en_DH-IH1-S",
    "beat": "en_B-IY1-T",
    "tonight": "en_T-AH0-N-AY1-T",
    "music": "en_M-Y-UW1-Z-IH0-K",
    "dance": "en_D-AE1-N-S",
    "dancing": "en_D-AE1-N-S-IH0-NG",
    "through": "en_TH-R-UW1",
    "cosmic": "en_K-AA1-Z-M-IH0-K",
    "journey": "en_JH-ER1-N-IY0",
}


# ============================================================================
# STYLE CONFIGURATION
# ============================================================================

@dataclass
class VocalStyle:
    """Configuration for vocal delivery style"""
    name: str
    
    # Melodic parameters
    pitch_variation: str  # "minimal", "narrow", "wide"
    pitch_range: int  # semitones
    base_pitch: int  # MIDI note
    
    # Rhythmic parameters
    rhythm_type: str  # "even", "varied", "syncopated", "speech"
    avg_duration: float  # seconds
    duration_variance: float  # 0.0-1.0
    
    # Expressiveness
    vibrato_depth: float  # Hz
    vibrato_rate: float  # Hz
    portamento: bool  # smooth pitch slides
    
    # Phrasing
    phrase_length: int  # notes per phrase
    breathing_breaks: bool


# Preset styles
STYLE_PRESETS = {
    "robotic": VocalStyle(
        name="Robotic/Monotone",
        pitch_variation="minimal",
        pitch_range=0,
        base_pitch=57,
        rhythm_type="even",
        avg_duration=0.25,
        duration_variance=0.0,
        vibrato_depth=0.0,
        vibrato_rate=0.0,
        portamento=False,
        phrase_length=100,  # No breaks
        breathing_breaks=False
    ),
    
    "singing": VocalStyle(
        name="Melodic Singing",
        pitch_variation="wide",
        pitch_range=12,
        base_pitch=57,
        rhythm_type="varied",
        avg_duration=0.4,
        duration_variance=0.5,
        vibrato_depth=5.0,
        vibrato_rate=5.0,
        portamento=True,
        phrase_length=4,
        breathing_breaks=True
    ),
    
    "speech": VocalStyle(
        name="Natural Speech",
        pitch_variation="narrow",
        pitch_range=3,
        base_pitch=57,
        rhythm_type="speech",
        avg_duration=0.25,
        duration_variance=0.3,
        vibrato_depth=1.0,
        vibrato_rate=3.0,
        portamento=False,
        phrase_length=5,
        breathing_breaks=True
    ),
    
    "rap": VocalStyle(
        name="Rap Flow",
        pitch_variation="minimal",
        pitch_range=3,
        base_pitch=56,
        rhythm_type="syncopated",
        avg_duration=0.15,
        duration_variance=0.2,
        vibrato_depth=0.0,
        vibrato_rate=0.0,
        portamento=False,
        phrase_length=8,
        breathing_breaks=False
    ),
    
    "expressive": VocalStyle(
        name="Expressive/Emotional",
        pitch_variation="wide",
        pitch_range=15,
        base_pitch=60,
        rhythm_type="varied",
        avg_duration=0.5,
        duration_variance=0.7,
        vibrato_depth=8.0,
        vibrato_rate=6.0,
        portamento=True,
        phrase_length=3,
        breathing_breaks=True
    )
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def midi_to_hz(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz"""
    return 440.0 * (2 ** ((midi_note - 69) / 12))


def lyrics_to_phonemes(lyrics: str) -> Tuple[List[str], List[str]]:
    """
    Convert lyrics to phonemes using CMU dictionary
    Returns: (phoneme_list, word_list) - one-to-one mapping
    
    CRITICAL: One word = one phoneme entry (not syllable splitting!)
    """
    words = lyrics.lower().split()
    phonemes = []
    valid_words = []
    
    for word in words:
        # Handle <SP> markers
        if word == "<sp>" or word == "<SP>":
            phonemes.append("<SP>")
            valid_words.append("<SP>")
        elif word in CMU_DICT:
            phonemes.append(CMU_DICT[word])
            valid_words.append(word)
        else:
            # Unknown word - use placeholder or skip
            print(f"Warning: '{word}' not in dictionary, skipping")
            
    return phonemes, valid_words


# Phones that are produced without vocal-fold vibration → F0 = 0 in real audio
VOICELESS_PHONES = frozenset({
    'P', 'T', 'K',          # voiceless stops
    'F', 'TH', 'S', 'SH',   # voiceless fricatives
    'HH',                    # glottal fricative
    'CH',                    # voiceless affricate
})


def _get_phones(phoneme: str) -> List[str]:
    """Extract the list of base phones (stress stripped) from a phoneme entry."""
    if phoneme == "<SP>":
        return []
    parts = phoneme.split("_", 1)
    raw = parts[1] if len(parts) == 2 else phoneme
    return [p.rstrip('012') for p in raw.split("-")]


def _boundary_silence_frames(phoneme: str, note_type: int = 2) -> Tuple[int, int]:
    """
    How many F0=0.0 frames to place at the onset / offset of a word.

    In real speech & singing the F0 tracker returns 0 during voiceless
    consonants and at inter-word pauses.  The reference en_target.json
    shows 2-5 zero frames at most word boundaries.

    Returns (onset_frames, offset_frames).
    """
    if phoneme == "<SP>":
        return (0, 0)

    phones = _get_phones(phoneme)
    if not phones:
        return (2, 0)

    first, last = phones[0], phones[-1]

    # --- onset ---
    if first in VOICELESS_PHONES:
        onset = 3          # voiceless consonant: ~60 ms of silence
    elif first not in {'AA', 'AE', 'AH', 'AO', 'AW', 'AY',
                        'EH', 'ER', 'EY', 'IH', 'IY',
                        'OW', 'OY', 'UH', 'UW'}:
        onset = 2          # voiced consonant: ~40 ms word-boundary gap
    else:
        onset = 1          # vowel-initial: brief glottal onset

    # --- offset ---
    if last in VOICELESS_PHONES:
        offset = 2         # voiceless ending: ~40 ms
    else:
        offset = 0         # voiced ending: F0 continues to boundary

    return (onset, offset)


def count_phones(phoneme: str) -> int:
    """
    Count individual phones in a phoneme entry like 'en_T-AH0-N-AY1-T'
    
    Each hyphen-separated segment is one phone.
    Examples:
        en_HH-UW1       → 2 phones (HH, UW1)
        en_L-AH1-V      → 3 phones (L, AH1, V)
        en_T-AH0-N-AY1-T → 5 phones (T, AH0, N, AY1, T)
        en_M-Y-UW1-Z-IH0-K → 6 phones (M, Y, UW1, Z, IH0, K)
        en_B-Y-UW1-T-AH0-F-AH0-L → 8 phones (B, Y, UW1, T, AH0, F, AH0, L)
    """
    if phoneme == "<SP>":
        return 0
    # Remove language prefix (en_, zh_, etc.)
    parts = phoneme.split("_", 1)
    if len(parts) == 2:
        phone_part = parts[1]
    else:
        phone_part = phoneme
    return len(phone_part.split("-"))


def generate_melody_from_style(
    num_notes: int, 
    style: VocalStyle,
    melody_hint: List[int] = None
) -> List[int]:
    """
    Generate pitch sequence based on style parameters
    """
    if melody_hint and len(melody_hint) == num_notes:
        # Use provided melody
        base_melody = melody_hint
    else:
        # Generate basic melody
        base_melody = [style.base_pitch] * num_notes
    
    # Apply style variations
    if style.pitch_variation == "minimal":
        # Robotic - all same pitch
        return [style.base_pitch] * num_notes
        
    elif style.pitch_variation == "narrow":
        # Speech-like or rap - slight variations
        pitches = []
        for i in range(num_notes):
            variation = random.randint(-1, 1)
            pitches.append(style.base_pitch + variation)
        return pitches
        
    elif style.pitch_variation == "wide":
        # Singing - use melodic contours
        if melody_hint:
            return melody_hint
        else:
            # Generate simple melodic pattern
            pitches = []
            current_pitch = style.base_pitch
            
            for i in range(num_notes):
                # Create melodic movement
                if i % 4 == 0:
                    jump = random.choice([0, 2, 3, 5, 7])  # Musical intervals
                else:
                    jump = random.choice([-2, -1, 0, 1, 2])
                    
                current_pitch = style.base_pitch + jump
                # Keep within range
                current_pitch = max(style.base_pitch - 5, 
                                   min(style.base_pitch + style.pitch_range, current_pitch))
                pitches.append(current_pitch)
                
            return pitches
    
    return base_melody


def generate_durations(
    num_notes: int,
    style: VocalStyle,
    phonemes: List[str] = None
) -> List[float]:
    """
    Generate note durations based on style, scaled by phone count.
    
    If phonemes are provided, duration of each word is proportional to
    the number of phones it contains.  avg_duration is treated as the
    target for a typical 3-phone word.
    """
    REFERENCE_PHONE_COUNT = 3
    MIN_PER_PHONE_DURATION = 0.06
    
    def _phone_scale(idx: int) -> float:
        if phonemes and idx < len(phonemes):
            pc = count_phones(phonemes[idx])
            return pc / REFERENCE_PHONE_COUNT if pc > 0 else 1.0
        return 1.0
    
    durations = []
    for i in range(num_notes):
        scale = _phone_scale(i)
        
        if style.rhythm_type == "even":
            dur = style.avg_duration * scale
        elif style.rhythm_type == "syncopated":
            pattern = [0.15, 0.1, 0.15, 0.1, 0.2]
            dur = pattern[i % len(pattern)] * scale
        elif style.rhythm_type == "speech":
            base = style.avg_duration * scale
            dur = random.uniform(base * 0.7, base * 1.3)
        else:  # "varied" - singing
            base = style.avg_duration * scale
            variance = random.uniform(-style.duration_variance, style.duration_variance)
            dur = base + (base * variance)
        
        # Enforce per-phone minimum
        if phonemes and i < len(phonemes):
            pc = count_phones(phonemes[i])
            min_dur = MIN_PER_PHONE_DURATION * pc if pc > 0 else 0.10
        else:
            min_dur = 0.10
        dur = max(min_dur, min(2.0, dur))
        durations.append(round(dur, 2))
    
    return durations


def generate_f0_contour(
    note_pitches: List[int],
    durations: List[float],
    style: VocalStyle,
    phonemes: List[str] = None,
    note_types: List[int] = None,
    f0_sample_rate: float = 50.0  # Hz (50 samples per second)
) -> List[float]:
    """
    Generate F0 contour with vibrato, portamento, and **natural word-
    boundary silence** (onset / offset F0=0.0 frames).

    In real speech & singing, voiceless consonants and inter-word gaps
    produce F0=0.  Without these gaps the model cannot detect word
    boundaries in melody mode, causing it to blur adjacent words.

    Uses **cumulative rounding** so the total number of F0 samples
    exactly equals  round(sum(durations) * sample_rate).
    """
    f0_contour = []
    cumulative_duration = 0.0

    for i, (pitch, dur) in enumerate(zip(note_pitches, durations)):
        cumulative_duration += dur
        # Target total samples up to the end of this entry
        target_total = round(cumulative_duration * f0_sample_rate)
        num_samples = max(1, target_total - len(f0_contour))

        if pitch == 0:  # Rest / <SP>
            f0_contour.extend([0.0] * num_samples)
            continue

        # ---- word-boundary silence (onset + offset) ----
        onset_frames = 0
        offset_frames = 0
        if phonemes and i < len(phonemes):
            nt = note_types[i] if note_types and i < len(note_types) else 2
            onset_frames, offset_frames = _boundary_silence_frames(
                phonemes[i], nt
            )
            # Never let silence exceed 40 % of the word's frames
            max_silence = num_samples * 2 // 5
            total_silence = onset_frames + offset_frames
            if total_silence > max_silence:
                scale = max_silence / total_silence
                onset_frames = int(onset_frames * scale)
                offset_frames = int(offset_frames * scale)

        voiced_frames = num_samples - onset_frames - offset_frames
        voiced_frames = max(1, voiced_frames)

        # ---- onset silence ----
        f0_contour.extend([0.0] * onset_frames)

        # ---- voiced portion ----
        base_f0 = midi_to_hz(pitch)

        for sample_idx in range(voiced_frames):
            t = (sample_idx / max(1, voiced_frames - 1)
                 if voiced_frames > 1 else 0.0)

            f0_value = base_f0

            # Add vibrato
            if style.vibrato_depth > 0:
                vibrato_phase = 2 * math.pi * style.vibrato_rate * t
                vibrato = style.vibrato_depth * math.sin(vibrato_phase)
                f0_value += vibrato

            # Add portamento (smooth slide to next note)
            if style.portamento and i < len(note_pitches) - 1:
                next_pitch = note_pitches[i + 1]
                if next_pitch != 0:
                    next_f0 = midi_to_hz(next_pitch)
                    if t > 0.7:
                        slide_progress = (t - 0.7) / 0.3
                        f0_value = (base_f0
                                    + (next_f0 - base_f0) * slide_progress)

            f0_contour.append(round(f0_value, 1))

        # ---- offset silence ----
        f0_contour.extend([0.0] * offset_frames)

    return f0_contour


def generate_note_types(
    num_notes: int,
    style: VocalStyle,
    has_final_rest: bool = True
) -> List[int]:
    """
    Generate note type markers (1=rest, 2=regular, 3=phrase end).

    IMPORTANT:  Type 3 marks *musical* phrase endings — specific melodic
    resolution points — NOT every word before a <SP>.  The reference
    en_target.json shows that many words before <SP> are type 2, and
    type 3 can appear mid-phrase at melodic cadence points.

    Without real melodic analysis we cannot determine where type 3
    belongs, so we default to type 2 for all pitched notes.  Users can
    override specific entries via melody_guide / post-processing.
    """
    note_types = []

    for i in range(num_notes):
        note_types.append(2)  # Regular note for all entries

    # Add final rest if requested
    if has_final_rest:
        note_types.append(1)

    return note_types


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_metadata(
    lyrics: str,
    style: str = "singing",
    bpm: int = 128,
    melody_guide: List[int] = None,
    custom_style: VocalStyle = None,
    add_phrase_breaks: bool = True
) -> Dict:
    """
    Generate complete SoulX-Singer metadata
    
    Args:
        lyrics: Text to sing/speak (can include <SP> markers)
        style: Preset name ("robotic", "singing", "speech", "rap", "expressive")
        bpm: Tempo (currently informational)
        melody_guide: Optional MIDI note sequence
        custom_style: Optional custom VocalStyle object
        add_phrase_breaks: Auto-add <SP> markers for phrasing
    
    Returns:
        Dictionary with complete metadata in SoulX-Singer format
    """
    
    # Get style configuration
    if custom_style:
        style_config = custom_style
    else:
        style_config = STYLE_PRESETS.get(style, STYLE_PRESETS["singing"])
    
    print(f"\n{'='*60}")
    print(f"Generating metadata with style: {style_config.name}")
    print(f"{'='*60}\n")
    
    # 1. Add phrase breaks if needed
    if add_phrase_breaks and style_config.breathing_breaks:
        words = lyrics.split()
        processed_words = ["<SP>"]  # Start with <SP>
        
        for i, word in enumerate(words):
            processed_words.append(word)
            # Add <SP> at phrase boundaries
            if (i + 1) % style_config.phrase_length == 0 and i < len(words) - 1:
                processed_words.append("<SP>")
        
        processed_words.append("<SP>")  # End with <SP>
        lyrics_with_breaks = " ".join(processed_words)
    else:
        # Use lyrics as-is
        lyrics_with_breaks = lyrics
        if not lyrics_with_breaks.startswith("<SP>"):
            lyrics_with_breaks = "<SP> " + lyrics_with_breaks
        if not lyrics_with_breaks.endswith("<SP>"):
            lyrics_with_breaks = lyrics_with_breaks + " <SP>"
    
    print(f"Processed lyrics: {lyrics_with_breaks}")
    
    # 2. Convert to phonemes (one word = one phoneme)
    phonemes, words_list = lyrics_to_phonemes(lyrics_with_breaks)
    num_entries = len(phonemes)
    
    print(f"Total entries: {num_entries} (words + <SP> markers)")
    
    # 3. Generate pitch sequence
    note_pitches = []
    for i, phoneme in enumerate(phonemes):
        if phoneme == "<SP>":
            # <SP> can have pitch=0 OR a pitch (for melodic phrasing)
            # Working example shows both patterns - using 0 for simplicity
            note_pitches.append(0)
        else:
            if melody_guide and len(melody_guide) > len([p for p in note_pitches if p != 0]):
                # Use provided melody
                melody_idx = len([p for p in note_pitches if p != 0])
                note_pitches.append(melody_guide[melody_idx])
            else:
                # Generate based on style
                if style_config.pitch_variation == "minimal":
                    note_pitches.append(style_config.base_pitch)
                elif style_config.pitch_variation == "narrow":
                    note_pitches.append(style_config.base_pitch + random.randint(-1, 1))
                else:  # wide
                    # Generate melodic pitch
                    base = style_config.base_pitch
                    variation = random.choice([0, 2, 3, 5, 7, -2, -3])
                    pitch = base + variation
                    pitch = max(base - 5, min(base + style_config.pitch_range, pitch))
                    note_pitches.append(pitch)
    
    if note_pitches:
        non_zero = [p for p in note_pitches if p != 0]
        if non_zero:
            print(f"Pitch range: MIDI {min(non_zero)} to {max(non_zero)}")
    
    # 4. Generate durations (SCALED BY PHONE COUNT!)
    # avg_duration is calibrated for a typical 3-phone word.
    # Words with more phones get proportionally more time so every
    # phone can be articulated properly.
    REFERENCE_PHONE_COUNT = 3
    MIN_PER_PHONE_DURATION = 0.06  # seconds — absolute floor per phone
    
    durations = []
    for i, phoneme in enumerate(phonemes):
        if phoneme == "<SP>":
            # <SP> gets a short duration (pause)
            durations.append(round(random.uniform(0.15, 0.3), 2))
        else:
            # Scale duration by number of phones in the word
            phone_count = count_phones(phoneme)
            phone_scale = phone_count / REFERENCE_PHONE_COUNT
            
            if style_config.rhythm_type == "even":
                dur = style_config.avg_duration * phone_scale
            elif style_config.rhythm_type == "syncopated":
                pattern = [0.15, 0.1, 0.15, 0.1, 0.2]
                base_dur = pattern[i % len(pattern)]
                dur = base_dur * phone_scale
            else:  # varied or speech
                base_dur = style_config.avg_duration * phone_scale
                variance = random.uniform(
                    -style_config.duration_variance,
                    style_config.duration_variance
                )
                dur = base_dur + (base_dur * variance)
            
            # Enforce minimum duration based on phone count
            min_dur = MIN_PER_PHONE_DURATION * phone_count
            dur = max(min_dur, min(2.0, dur))
            durations.append(round(dur, 2))
    
    print(f"Duration range: {min(durations):.2f}s to {max(durations):.2f}s")
    
    # 5. Generate note types
    #    Type 1 = rest (<SP>), Type 2 = regular note.
    #    Type 3 = musical phrase end — requires real melodic analysis to
    #    place correctly (see reference en_target.json where type 3 marks
    #    specific melodic cadence points, NOT every word before <SP>).
    #    Using type 3 incorrectly causes the model to garble words, so
    #    we default to type 2 for all pitched entries.
    note_types = []
    for i, phoneme in enumerate(phonemes):
        if phoneme == "<SP>":
            note_types.append(1)  # Rest marker
        else:
            note_types.append(2)  # Regular note
    
    # 6. Generate F0 contour (with word-boundary silence for melody mode)
    f0_contour = generate_f0_contour(
        note_pitches, durations, style_config,
        phonemes=phonemes, note_types=note_types
    )
    
    print(f"F0 samples: {len(f0_contour)}")
    print(f"F0 samples per entry: {len(f0_contour) / len(phonemes):.1f} average")
    
    # 7. Build text string from words
    text_string = " ".join(words_list)
    
    # 8. Build metadata
    # CRITICAL: derive time from F0 count so that  time / 20 == len(f0)
    # exactly (the working example satisfies this invariant).
    time_ms = len(f0_contour) * 20  # 20 ms per frame at 50 Hz
    
    metadata = {
        "index": f"generated_{style}_001",
        "language": "English",
        "time": [0, time_ms],
        "duration": " ".join([f"{d:.2f}" for d in durations]),
        "text": text_string,
        "phoneme": " ".join(phonemes),
        "note_pitch": " ".join(map(str, note_pitches)),
        "note_type": " ".join(map(str, note_types)),
        "f0": " ".join([f"{f:.1f}" for f in f0_contour])
    }
    
    print(f"\n✅ Metadata generated successfully!")
    print(f"Total duration: {sum(durations):.2f}s")
    print(f"{'='*60}\n")
    
    return metadata


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import os

    test_lyrics = "tonight love feel music"
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # Use a fixed seed for reproducible benchmarks
    random.seed(42)

    print("\n" + "="*70)
    print("SOULX-SINGER METADATA GENERATOR")
    print("="*70)

    styles = ["singing", "robotic", "speech", "rap", "expressive"]

    for style_name in styles:
        print(f"\n🎵 GENERATING {style_name.upper()} STYLE...")
        metadata = generate_metadata(
            lyrics=test_lyrics,
            style=style_name,
            bpm=128
        )

        output_path = os.path.join(output_dir, f"metadata_{style_name}.json")
        with open(output_path, 'w') as f:
            json.dump([metadata], f, indent=2)
        print(f"✅ Saved: {output_path}")

    print("\n" + "="*70)
    print("ALL STYLES GENERATED SUCCESSFULLY")
    print("="*70)
    print("""
Usage in your code:
   from metadata_generator import generate_metadata
   
   metadata = generate_metadata(
       lyrics="your lyrics here",
       style="singing"  # or "robotic", "speech", "rap", "expressive"
   )
    """)

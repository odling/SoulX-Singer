# SoulX-Singer Metadata Generator - Usage Guide

## 📋 Quick Start

### Generate All Styles at Once

```bash
python3 generate_all_styles.py "you can do it every day"
```

This will create 5 JSON files:
- `metadata_robotic.json` - Flat, monotone delivery
- `metadata_singing.json` - Melodic with vibrato
- `metadata_speech.json` - Natural speech rhythm
- `metadata_rap.json` - Fast, rhythmic flow
- `metadata_expressive.json` - Very emotional, wide range

---

## 🎛️ Generate Individual Styles

### Method 1: Using Python directly

```python
from metadata_generator import generate_metadata
import json

# Generate singing style
metadata = generate_metadata(
    lyrics="you can do it every day",
    style="singing",
    bpm=128
)

# Save to file
with open("my_vocal.json", 'w') as f:
    json.dump([metadata], f, indent=2)
```

### Method 2: Command Line (modify generate_all_styles.py)

Edit line 40 in `generate_all_styles.py` to generate only the style you want:

```python
# Change this line:
styles = ["robotic", "singing", "speech", "rap", "expressive"]

# To just one style:
styles = ["singing"]
```

Then run:
```bash
python3 generate_all_styles.py "your lyrics here"
```

---

## 🎵 Style Characteristics

### 1. ROBOTIC
```python
metadata = generate_metadata(lyrics="test", style="robotic")
```
**Characteristics:**
- Flat pitch (no variation)
- Mechanical timing (even rhythm)
- No vibrato
- No breathing breaks
- **Use for:** Vocoder effects, Daft Punk style, synth vocals

### 2. SINGING
```python
metadata = generate_metadata(lyrics="test", style="singing")
```
**Characteristics:**
- Wide melodic range (12 semitones)
- Varied rhythm
- 5 Hz vibrato
- Natural phrase breaks every 4 words
- **Use for:** Pop, house, melodic vocals

### 3. SPEECH
```python
metadata = generate_metadata(lyrics="test", style="speech")
```
**Characteristics:**
- Narrow pitch range (3 semitones)
- Natural speech rhythm
- Minimal vibrato (1 Hz)
- Phrase breaks every 5 words
- **Use for:** Spoken word, narration, conversational

### 4. RAP
```python
metadata = generate_metadata(lyrics="test", style="rap")
```
**Characteristics:**
- Minimal pitch variation
- Fast, syncopated rhythm
- No vibrato
- Continuous flow (no breaks)
- **Use for:** Rap, hip-hop, rhythmic delivery

### 5. EXPRESSIVE
```python
metadata = generate_metadata(lyrics="test", style="expressive")
```
**Characteristics:**
- Very wide range (15 semitones)
- High vibrato (8 Hz)
- Varied durations
- Frequent phrase breaks (every 3 words)
- **Use for:** Emotional ballads, dramatic vocals

---

## 🎹 Custom Melody

Provide your own MIDI note sequence:

```python
custom_melody = [60, 62, 64, 65, 67, 65, 64, 62, 60]  # C major scale

metadata = generate_metadata(
    lyrics="you can do it every day you can be",
    style="singing",
    melody_guide=custom_melody
)
```

**Note:** Melody must have enough notes for all words (excluding <SP> markers)

---

## 🔧 Advanced Usage

### Custom Style Parameters

```python
from metadata_generator import VocalStyle, generate_metadata

# Create custom style
my_style = VocalStyle(
    name="My Custom Style",
    pitch_variation="wide",      # "minimal", "narrow", "wide"
    pitch_range=10,               # semitones
    base_pitch=60,                # MIDI note (C4)
    rhythm_type="varied",         # "even", "varied", "syncopated", "speech"
    avg_duration=0.35,            # seconds
    duration_variance=0.4,        # 0.0-1.0
    vibrato_depth=3.0,            # Hz
    vibrato_rate=5.0,             # Hz
    portamento=True,              # smooth pitch slides
    phrase_length=4,              # words per phrase
    breathing_breaks=True         # add <SP> markers
)

# Generate with custom style
metadata = generate_metadata(
    lyrics="test lyrics",
    custom_style=my_style
)
```

### Manual Phrase Breaks

Add `<SP>` markers manually in your lyrics:

```python
lyrics = "you can do it <SP> every single day <SP>"

metadata = generate_metadata(
    lyrics=lyrics,
    style="singing",
    add_phrase_breaks=False  # Don't auto-add breaks
)
```

---

## 📝 Example Commands

### Tech House Vocal Hook
```bash
python3 -c "
from metadata_generator import generate_metadata
import json

metadata = generate_metadata(
    lyrics='feel the beat tonight',
    style='singing',
    melody_guide=[57, 60, 62, 65, 62, 60]
)

with open('tech_house_hook.json', 'w') as f:
    json.dump([metadata], f, indent=2)
print('✅ Generated: tech_house_hook.json')
"
```

### Robotic Vocoder Effect
```bash
python3 -c "
from metadata_generator import generate_metadata
import json

metadata = generate_metadata(
    lyrics='around the world around the world',
    style='robotic'
)

with open('vocoder_vocal.json', 'w') as f:
    json.dump([metadata], f, indent=2)
print('✅ Generated: vocoder_vocal.json')
"
```

### Rap Verse
```bash
python3 -c "
from metadata_generator import generate_metadata
import json

metadata = generate_metadata(
    lyrics='i got the flow i got the rhythm yeah',
    style='rap'
)

with open('rap_verse.json', 'w') as f:
    json.dump([metadata], f, indent=2)
print('✅ Generated: rap_verse.json')
"
```

---

## ⚠️ Important Notes

### Phoneme Dictionary
The generator includes common words in CMU phoneme dictionary. If you get warnings about unknown words:

1. Add them to the `CMU_DICT` in `metadata_generator.py`
2. Or use simpler/more common words

### F0 Sample Rate
F0 is generated at 50 Hz (50 samples per second). This matches the working example and provides smooth pitch contours.

### Testing with SoulX-Singer
After generating metadata:

```bash
# Use with SoulX-Singer
python3 soulx_inference.py \
  --prompt_audio "path/to/voice_reference.wav" \
  --prompt_metadata "path/to/voice_metadata.json" \
  --target_metadata "metadata_singing.json" \
  --output "output_vocal.wav"
```

---

## 🎯 Quick Reference: Style Selection

| Want This | Use Style | Characteristics |
|-----------|-----------|----------------|
| Pop/House vocals | `singing` | Melodic, vibrato, natural |
| Daft Punk vocoder | `robotic` | Flat, mechanical |
| Spoken word | `speech` | Conversational, natural rhythm |
| Hip-hop verse | `rap` | Fast, rhythmic, minimal pitch |
| Emotional ballad | `expressive` | Wide range, high vibrato |

---

## 📚 Full Example Workflow

```python
#!/usr/bin/env python3
from metadata_generator import generate_metadata
import json

# 1. Define your lyrics
lyrics = "dancing through the cosmic night"

# 2. Define your melody (optional)
melody = [57, 60, 62, 65, 67, 65, 62, 60]

# 3. Generate metadata
metadata = generate_metadata(
    lyrics=lyrics,
    style="singing",
    melody_guide=melody,
    bpm=128
)

# 4. Save to file
with open("my_vocal.json", 'w') as f:
    json.dump([metadata], f, indent=2)

print("✅ Generated: my_vocal.json")
print(f"Duration: {sum(float(d) for d in metadata['duration'].split()):.2f}s")
print(f"Pitch range: {metadata['note_pitch']}")

# 5. Use with SoulX-Singer
# (see SoulX-Singer documentation for synthesis)
```

---

## 🔍 Troubleshooting

**Q: Words not pronouncing correctly?**
A: Check if the word is in `CMU_DICT`. Add it if missing.

**Q: Output sounds robotic even with "singing" style?**
A: Make sure your prompt audio (voice reference) has natural characteristics.

**Q: Too many/few phrase breaks?**
A: Adjust `phrase_length` parameter or manually add `<SP>` markers.

**Q: Melody doesn't match my intention?**
A: Provide explicit `melody_guide` parameter with MIDI notes.

---

## 📞 Support

For issues or questions about SoulX-Singer synthesis, refer to:
- SoulX-Singer documentation
- GitHub issues: https://github.com/Soul-AILab/SoulX-Singer

This generator creates the TARGET metadata. You still need:
1. Prompt audio (voice reference)
2. Prompt metadata (from preprocessing)
3. SoulX-Singer model for synthesis

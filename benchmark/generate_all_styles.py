#!/usr/bin/env python3
"""
Simple CLI for generating SoulX-Singer metadata
"""

from metadata_generator import generate_metadata
import json
import sys

def generate_style(lyrics, style_name, output_file=None):
    """Generate metadata for a specific style"""
    
    metadata = generate_metadata(
        lyrics=lyrics,
        style=style_name,
        bpm=128
    )
    
    if output_file is None:
        output_file = f"metadata_{style_name}.json"
    
    with open(output_file, 'w') as f:
        json.dump([metadata], f, indent=2)
    
    print(f"✅ Saved: {output_file}\n")
    return metadata


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SOULX-SINGER METADATA GENERATOR")
    print("="*70 + "\n")
    
    # Default lyrics if none provided
    if len(sys.argv) > 1:
        lyrics = " ".join(sys.argv[1:])
    else:
        lyrics = "you can do it every day"
    
    print(f"Lyrics: {lyrics}\n")
    print("="*70)
    
    # Generate all styles
    styles = ["robotic", "singing", "speech", "rap", "expressive"]
    
    for style in styles:
        print(f"\n🎵 Generating {style.upper()} style...")
        generate_style(lyrics, style)
    
    print("\n" + "="*70)
    print("✅ ALL STYLES GENERATED!")
    print("="*70)
    print("\nGenerated files:")
    for style in styles:
        print(f"  - metadata_{style}.json")
    print("\nUse these with SoulX-Singer for synthesis!")

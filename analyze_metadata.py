#!/usr/bin/env python3
"""
Comprehensive statistical analysis of English metadata JSON files
under example-metadata-target/
"""

import json
import os
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

BASE_DIR = Path("/Users/onur/Documents/projects/SoulX-Singer/example-metadata-target")

def load_all_english_json_files():
    """Load all English JSON files from all subdirectories."""
    files = []
    errors = []
    for root, dirs, filenames in os.walk(BASE_DIR):
        for fname in sorted(filenames):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, BASE_DIR)
            try:
                with open(fpath, "r") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        if entry.get("language") == "English":
                            files.append((rel_path, entry))
                elif isinstance(data, dict):
                    if data.get("language") == "English":
                        files.append((rel_path, data))
            except Exception as e:
                errors.append((rel_path, str(e)))
    return files, errors


def analyze_phonemes(entries):
    """Analyze phoneme format and tokens."""
    print("=" * 80)
    print("1. PHONEME FORMAT ANALYSIS")
    print("=" * 80)

    all_phoneme_tokens = Counter()
    individual_symbols = set()
    prefixed_tokens = []
    special_tokens = set()

    for rel_path, entry in entries:
        phonemes = entry["phoneme"].strip().split()
        for ph in phonemes:
            all_phoneme_tokens[ph] += 1
            if ph.startswith("<") and ph.endswith(">"):
                special_tokens.add(ph)
            elif ph.startswith("en_"):
                prefixed_tokens.append(ph)
                # Extract individual symbols: strip "en_" prefix, split by "-"
                inner = ph[3:]  # strip "en_"
                symbols = inner.split("-")
                for s in symbols:
                    individual_symbols.add(s)

    print(f"\n  Total unique phoneme tokens: {len(all_phoneme_tokens)}")
    print(f"  Total occurrences across all files: {sum(all_phoneme_tokens.values())}")

    print(f"\n  Special tokens: {sorted(special_tokens)}")
    for st in sorted(special_tokens):
        print(f"    {st}: {all_phoneme_tokens[st]} occurrences")

    print(f"\n  Unique en_* prefixed tokens: {len([t for t in all_phoneme_tokens if t.startswith('en_')])}")
    print(f"\n  Top 30 most common phoneme tokens:")
    for token, count in all_phoneme_tokens.most_common(30):
        print(f"    {token:30s} : {count}")

    print(f"\n  All unique individual phoneme symbols ({len(individual_symbols)}):")
    # Separate vowels (with stress marks) and consonants
    vowels = sorted([s for s in individual_symbols if any(c.isdigit() for c in s)])
    consonants = sorted([s for s in individual_symbols if not any(c.isdigit() for c in s)])
    print(f"    Vowels (with stress): {vowels}")
    print(f"    Consonants:           {consonants}")

    print(f"\n  Phoneme structure pattern: en_<symbol1>-<symbol2>-...-<symbolN>")
    # Show length distribution of dash-separated parts
    part_counts = Counter()
    for ph in prefixed_tokens:
        inner = ph[3:]
        n_parts = len(inner.split("-"))
        part_counts[n_parts] += 1
    print(f"  Number of symbols per phoneme token (distribution):")
    for n in sorted(part_counts.keys()):
        print(f"    {n} symbol(s): {part_counts[n]} occurrences ({100*part_counts[n]/len(prefixed_tokens):.1f}%)")

    return all_phoneme_tokens


def analyze_note_types(entries):
    """Analyze note_type distribution and patterns."""
    print("\n" + "=" * 80)
    print("2. NOTE TYPE ANALYSIS")
    print("=" * 80)

    type_counts = Counter()
    type_for_sp = Counter()
    type_for_ap = Counter()
    type_for_words = Counter()
    type_before_sp = Counter()
    type_after_sp = Counter()
    type_before_ap = Counter()
    type_after_ap = Counter()

    slur_context = []  # (prev_type, next_type) around type 3

    for rel_path, entry in entries:
        texts = entry["text"].strip().split()
        types = list(map(int, entry["note_type"].strip().split()))
        phonemes = entry["phoneme"].strip().split()

        assert len(texts) == len(types) == len(phonemes), \
            f"Mismatch in {rel_path}: text={len(texts)}, types={len(types)}, phonemes={len(phonemes)}"

        for i, (txt, typ, ph) in enumerate(zip(texts, types, phonemes)):
            type_counts[typ] += 1

            if txt == "<SP>":
                type_for_sp[typ] += 1
            elif txt == "<AP>":
                type_for_ap[typ] += 1
            else:
                type_for_words[typ] += 1

            # Before/after patterns for <SP>
            if txt == "<SP>":
                if i > 0:
                    type_before_sp[types[i - 1]] += 1
                if i < len(types) - 1:
                    type_after_sp[types[i + 1]] += 1

            if txt == "<AP>":
                if i > 0:
                    type_before_ap[types[i - 1]] += 1
                if i < len(types) - 1:
                    type_after_ap[types[i + 1]] += 1

            # Slur (type 3) context
            if typ == 3:
                prev_t = types[i - 1] if i > 0 else None
                next_t = types[i + 1] if i < len(types) - 1 else None
                prev_txt = texts[i - 1] if i > 0 else None
                next_txt = texts[i + 1] if i < len(types) - 1 else None
                slur_context.append((prev_t, prev_txt, next_t, next_txt, txt, ph, rel_path))

    print(f"\n  Overall note_type distribution:")
    for typ in sorted(type_counts.keys()):
        pct = 100 * type_counts[typ] / sum(type_counts.values())
        print(f"    Type {typ}: {type_counts[typ]:6d} ({pct:.1f}%)")

    print(f"\n  note_type for <SP> entries: {dict(sorted(type_for_sp.items()))}")
    print(f"  note_type for <AP> entries: {dict(sorted(type_for_ap.items()))}")
    print(f"  note_type for regular words: {dict(sorted(type_for_words.items()))}")

    print(f"\n  Types appearing BEFORE <SP>: {dict(sorted(type_before_sp.items()))}")
    print(f"  Types appearing AFTER  <SP>: {dict(sorted(type_after_sp.items()))}")
    print(f"  Types appearing BEFORE <AP>: {dict(sorted(type_before_ap.items()))}")
    print(f"  Types appearing AFTER  <AP>: {dict(sorted(type_after_ap.items()))}")

    print(f"\n  Slur (type 3) analysis:")
    print(f"    Total type 3 occurrences: {type_counts.get(3, 0)}")
    if slur_context:
        prev_types = Counter(s[0] for s in slur_context if s[0] is not None)
        next_types = Counter(s[2] for s in slur_context if s[2] is not None)
        print(f"    Type preceding slur: {dict(sorted(prev_types.items()))}")
        print(f"    Type following slur: {dict(sorted(next_types.items()))}")
        print(f"    Example slur contexts (first 10):")
        for ctx in slur_context[:10]:
            prev_t, prev_txt, next_t, next_txt, txt, ph, fp = ctx
            print(f"      prev=({prev_t}, '{prev_txt}') -> slur('{txt}', {ph}) -> next=({next_t}, '{next_txt}')  [{fp}]")
    else:
        print(f"    No type 3 (slur) found in any file.")


def analyze_durations(entries):
    """Analyze duration statistics."""
    print("\n" + "=" * 80)
    print("3. DURATION ANALYSIS")
    print("=" * 80)

    all_word_durations = []
    sp_durations = []
    ap_durations = []
    regular_durations = []
    file_total_durations = []

    for rel_path, entry in entries:
        texts = entry["text"].strip().split()
        durations = list(map(float, entry["duration"].strip().split()))

        assert len(texts) == len(durations), \
            f"Mismatch in {rel_path}: text={len(texts)}, dur={len(durations)}"

        file_total = sum(durations)
        file_total_durations.append((file_total, rel_path))

        for txt, dur in zip(texts, durations):
            all_word_durations.append(dur)
            if txt == "<SP>":
                sp_durations.append(dur)
            elif txt == "<AP>":
                ap_durations.append(dur)
            else:
                regular_durations.append(dur)

    def print_stats(name, data):
        if not data:
            print(f"\n  {name}: No data")
            return
        print(f"\n  {name} ({len(data)} entries):")
        print(f"    Min:    {min(data):.4f}s")
        print(f"    Max:    {max(data):.4f}s")
        print(f"    Mean:   {statistics.mean(data):.4f}s")
        print(f"    Median: {statistics.median(data):.4f}s")
        print(f"    Stdev:  {statistics.stdev(data):.4f}s" if len(data) > 1 else "")
        # Percentiles
        sorted_data = sorted(data)
        p5 = sorted_data[int(len(sorted_data) * 0.05)]
        p25 = sorted_data[int(len(sorted_data) * 0.25)]
        p75 = sorted_data[int(len(sorted_data) * 0.75)]
        p95 = sorted_data[int(len(sorted_data) * 0.95)]
        print(f"    P5:     {p5:.4f}s")
        print(f"    P25:    {p25:.4f}s")
        print(f"    P75:    {p75:.4f}s")
        print(f"    P95:    {p95:.4f}s")

    print_stats("All word/token durations", all_word_durations)
    print_stats("<SP> durations", sp_durations)
    print_stats("<AP> durations", ap_durations)
    print_stats("Regular word durations", regular_durations)

    totals = [t for t, _ in file_total_durations]
    print_stats("Total duration per file (sum of word durations)", totals)

    # Show shortest and longest files
    file_total_durations.sort()
    print(f"\n  5 shortest files (by sum of durations):")
    for total, fp in file_total_durations[:5]:
        print(f"    {total:.2f}s  {fp}")
    print(f"\n  5 longest files (by sum of durations):")
    for total, fp in file_total_durations[-5:]:
        print(f"    {total:.2f}s  {fp}")


def analyze_pitch(entries):
    """Analyze note_pitch values."""
    print("\n" + "=" * 80)
    print("4. PITCH ANALYSIS")
    print("=" * 80)

    all_pitches = Counter()
    nonzero_pitches = []
    sp_pitches = Counter()
    ap_pitches = Counter()
    word_pitches = Counter()

    for rel_path, entry in entries:
        texts = entry["text"].strip().split()
        pitches = list(map(int, entry["note_pitch"].strip().split()))

        for txt, pitch in zip(texts, pitches):
            all_pitches[pitch] += 1
            if pitch != 0:
                nonzero_pitches.append(pitch)
            if txt == "<SP>":
                sp_pitches[pitch] += 1
            elif txt == "<AP>":
                ap_pitches[pitch] += 1
            else:
                word_pitches[pitch] += 1

    print(f"\n  Total pitch entries: {sum(all_pitches.values())}")
    print(f"  Unique pitch values (including 0): {len(all_pitches)}")

    print(f"\n  Pitch=0 count: {all_pitches[0]} ({100*all_pitches[0]/sum(all_pitches.values()):.1f}%)")

    if nonzero_pitches:
        print(f"\n  Non-zero pitch range: {min(nonzero_pitches)} to {max(nonzero_pitches)}")
        print(f"  Non-zero pitch mean: {statistics.mean(nonzero_pitches):.1f}")
        print(f"  Non-zero pitch median: {statistics.median(nonzero_pitches):.1f}")

    # MIDI note to name mapping
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    def midi_to_name(midi):
        octave = (midi // 12) - 1
        note = note_names[midi % 12]
        return f"{note}{octave}"

    print(f"\n  Top 20 most common non-zero pitches (MIDI → Note Name):")
    nonzero_counter = Counter(nonzero_pitches)
    for pitch, count in nonzero_counter.most_common(20):
        pct = 100 * count / len(nonzero_pitches)
        print(f"    MIDI {pitch:3d} ({midi_to_name(pitch):4s}): {count:5d} ({pct:.1f}%)")

    print(f"\n  <SP> pitch distribution: {dict(sorted(sp_pitches.items()))}")
    sp_nonzero = {k: v for k, v in sp_pitches.items() if k != 0}
    if sp_nonzero:
        print(f"  WARNING: <SP> has non-zero pitches: {sp_nonzero}")
    else:
        print(f"  CONFIRMED: All <SP> entries have pitch=0")

    print(f"\n  <AP> pitch distribution: {dict(sorted(ap_pitches.items()))}")
    ap_nonzero = {k: v for k, v in ap_pitches.items() if k != 0}
    if ap_nonzero:
        print(f"  NOTE: <AP> has non-zero pitches: {ap_nonzero}")
    else:
        if ap_pitches:
            print(f"  CONFIRMED: All <AP> entries have pitch=0")
        else:
            print(f"  No <AP> entries found.")


def analyze_f0(entries):
    """Analyze F0 contour data."""
    print("\n" + "=" * 80)
    print("5. F0 ANALYSIS")
    print("=" * 80)

    all_f0_counts = []
    file_durations_and_f0_counts = []
    all_f0_values = []
    zero_count = 0
    nonzero_f0_values = []

    for rel_path, entry in entries:
        f0_values = list(map(float, entry["f0"].strip().split()))
        time_range = entry["time"]
        time_start, time_end = time_range[0], time_range[1]
        durations = list(map(float, entry["duration"].strip().split()))
        total_dur = sum(durations)

        n_samples = len(f0_values)
        all_f0_counts.append(n_samples)
        file_durations_and_f0_counts.append((total_dur, n_samples, time_start, time_end, rel_path))

        for v in f0_values:
            all_f0_values.append(v)
            if v == 0.0:
                zero_count += 1
            else:
                nonzero_f0_values.append(v)

    total_f0 = len(all_f0_values)
    print(f"\n  Total F0 samples across all files: {total_f0}")
    print(f"  F0 samples per file: min={min(all_f0_counts)}, max={max(all_f0_counts)}, "
          f"mean={statistics.mean(all_f0_counts):.1f}, median={statistics.median(all_f0_counts):.1f}")

    print(f"\n  F0 = 0.0 (silence/unvoiced): {zero_count} ({100*zero_count/total_f0:.1f}%)")
    print(f"  F0 > 0.0 (voiced):           {len(nonzero_f0_values)} ({100*len(nonzero_f0_values)/total_f0:.1f}%)")

    if nonzero_f0_values:
        print(f"\n  Voiced F0 range: {min(nonzero_f0_values):.1f} Hz to {max(nonzero_f0_values):.1f} Hz")
        print(f"  Voiced F0 mean:  {statistics.mean(nonzero_f0_values):.1f} Hz")
        print(f"  Voiced F0 median: {statistics.median(nonzero_f0_values):.1f} Hz")
        print(f"  Voiced F0 stdev: {statistics.stdev(nonzero_f0_values):.1f} Hz")

        # MIDI note equivalents for range
        import math
        min_midi = 69 + 12 * math.log2(min(nonzero_f0_values) / 440.0)
        max_midi = 69 + 12 * math.log2(max(nonzero_f0_values) / 440.0)
        print(f"  Voiced F0 range in MIDI: ~{min_midi:.1f} to ~{max_midi:.1f}")

    # F0 sampling rate estimation
    print(f"\n  F0 sampling rate estimation:")
    rates = []
    for total_dur, n_samples, t_start, t_end, fp in file_durations_and_f0_counts:
        if total_dur > 0:
            rate_from_dur = n_samples / total_dur
            rates.append(("sum_dur", rate_from_dur, fp))
        time_dur_sec = (t_end - t_start) / 1000.0 if t_end > t_start else None
        if time_dur_sec and time_dur_sec > 0:
            rate_from_time = n_samples / time_dur_sec
            rates.append(("time_field", rate_from_time, fp))

    # Group by method
    dur_rates = [r for m, r, _ in rates if m == "sum_dur"]
    time_rates = [r for m, r, _ in rates if m == "time_field"]

    if dur_rates:
        print(f"    Based on sum(duration): mean={statistics.mean(dur_rates):.2f} samples/sec, "
              f"median={statistics.median(dur_rates):.2f}, min={min(dur_rates):.2f}, max={max(dur_rates):.2f}")
    if time_rates:
        print(f"    Based on time field:    mean={statistics.mean(time_rates):.2f} samples/sec, "
              f"median={statistics.median(time_rates):.2f}, min={min(time_rates):.2f}, max={max(time_rates):.2f}")

    # Check time field interpretation
    print(f"\n  Time field analysis (first 10 files):")
    for total_dur, n_samples, t_start, t_end, fp in file_durations_and_f0_counts[:10]:
        time_dur_ms = t_end - t_start
        time_dur_sec = time_dur_ms / 1000.0
        print(f"    {fp[:60]:60s}  time=[{t_start},{t_end}] ({time_dur_sec:.2f}s)  "
              f"sum_dur={total_dur:.2f}s  f0_samples={n_samples}  "
              f"rate_from_time={n_samples/time_dur_sec:.1f}/s" if time_dur_sec > 0 else "")


def analyze_structure(entries):
    """Analyze structural patterns."""
    print("\n" + "=" * 80)
    print("6. STRUCTURE ANALYSIS")
    print("=" * 80)

    starts_with_sp = 0
    ends_with_sp = 0
    starts_and_ends_sp = 0
    word_counts = []
    not_starting_sp = []
    not_ending_sp = []

    for rel_path, entry in entries:
        texts = entry["text"].strip().split()
        word_counts.append(len(texts))

        starts = texts[0] == "<SP>"
        ends = texts[-1] == "<SP>"

        if starts:
            starts_with_sp += 1
        else:
            not_starting_sp.append((rel_path, texts[0]))
        if ends:
            ends_with_sp += 1
        else:
            not_ending_sp.append((rel_path, texts[-1]))
        if starts and ends:
            starts_and_ends_sp += 1

    total = len(entries)
    print(f"\n  Total English files analyzed: {total}")
    print(f"\n  Files starting with <SP>: {starts_with_sp}/{total} ({100*starts_with_sp/total:.1f}%)")
    print(f"  Files ending with <SP>:   {ends_with_sp}/{total} ({100*ends_with_sp/total:.1f}%)")
    print(f"  Files both start & end:   {starts_and_ends_sp}/{total} ({100*starts_and_ends_sp/total:.1f}%)")

    if not_starting_sp:
        print(f"\n  Files NOT starting with <SP> ({len(not_starting_sp)}):")
        for fp, first_token in not_starting_sp[:10]:
            print(f"    {fp}  starts with: '{first_token}'")
        if len(not_starting_sp) > 10:
            print(f"    ... and {len(not_starting_sp) - 10} more")

    if not_ending_sp:
        print(f"\n  Files NOT ending with <SP> ({len(not_ending_sp)}):")
        for fp, last_token in not_ending_sp[:10]:
            print(f"    {fp}  ends with: '{last_token}'")
        if len(not_ending_sp) > 10:
            print(f"    ... and {len(not_ending_sp) - 10} more")

    print(f"\n  Word entries per file:")
    print(f"    Min:    {min(word_counts)}")
    print(f"    Max:    {max(word_counts)}")
    print(f"    Mean:   {statistics.mean(word_counts):.1f}")
    print(f"    Median: {statistics.median(word_counts):.1f}")

    # Distribution histogram
    count_dist = Counter(word_counts)
    print(f"\n  Word count distribution:")
    for wc in sorted(count_dist.keys()):
        bar = "#" * count_dist[wc]
        print(f"    {wc:3d}: {count_dist[wc]:3d} {bar}")

    # Time field vs f0 samples relationship
    print(f"\n  Time field vs F0 analysis:")
    print(f"  Checking if time[1] = number_of_f0_samples (i.e., time is in sample indices)...")
    matches_samples = 0
    matches_ms = 0
    for rel_path, entry in entries[:20]:
        f0_values = entry["f0"].strip().split()
        n_f0 = len(f0_values)
        t_start, t_end = entry["time"]
        durations = list(map(float, entry["duration"].strip().split()))
        total_dur = sum(durations)
        time_span = t_end - t_start

        # Check different interpretations
        if time_span == n_f0:
            matches_samples += 1
        if abs(time_span / 1000.0 - total_dur) < 0.1:
            matches_ms += 1

        print(f"    {rel_path[:55]:55s}  time=[{t_start},{t_end}] span={time_span}  "
              f"f0_samples={n_f0}  sum_dur={total_dur:.2f}s  "
              f"span_as_sec={time_span/1000.0:.2f}  "
              f"ratio_span/f0={time_span/n_f0:.4f}" if n_f0 > 0 else "")

    print(f"\n  Among first 20 files:")
    print(f"    time_span == n_f0_samples: {matches_samples}")
    print(f"    time_span/1000 ≈ sum_dur:  {matches_ms}")

    # Check if time field is in some unit related to f0 hop size
    print(f"\n  Investigating time field units:")
    for rel_path, entry in entries[:5]:
        f0_values = entry["f0"].strip().split()
        n_f0 = len(f0_values)
        t_start, t_end = entry["time"]
        durations = list(map(float, entry["duration"].strip().split()))
        total_dur = sum(durations)
        time_span = t_end - t_start

        # Common hop sizes: 10ms, 5ms, 1/100s
        for hop_ms in [1, 5, 10, 20]:
            predicted_samples = time_span / hop_ms
            if abs(predicted_samples - n_f0) < 2:
                print(f"    {rel_path[:50]:50s}: time_span={time_span}, "
                      f"f0={n_f0}, hop={hop_ms}ms → predicted_f0={predicted_samples:.1f} ✓")

    # Deeper: what is time[1] in terms of f0?
    print(f"\n  Exact ratio: time_span / n_f0_samples for all files:")
    ratios = []
    for rel_path, entry in entries:
        f0_values = entry["f0"].strip().split()
        n_f0 = len(f0_values)
        t_start, t_end = entry["time"]
        time_span = t_end - t_start
        if n_f0 > 0:
            ratio = time_span / n_f0
            ratios.append(ratio)
    if ratios:
        print(f"    Min ratio:    {min(ratios):.6f}")
        print(f"    Max ratio:    {max(ratios):.6f}")
        print(f"    Mean ratio:   {statistics.mean(ratios):.6f}")
        print(f"    Median ratio: {statistics.median(ratios):.6f}")
        print(f"    → This suggests time is in units of ~{statistics.median(ratios):.1f} × f0_sample_count")
        if abs(statistics.median(ratios) - 20) < 2:
            print(f"    → Likely interpretation: time is in MILLISECONDS with 20ms F0 hop (50Hz F0 rate)")
        elif abs(statistics.median(ratios) - 10) < 2:
            print(f"    → Likely interpretation: time is in MILLISECONDS with 10ms F0 hop (100Hz F0 rate)")
        elif abs(statistics.median(ratios) - 1) < 0.5:
            print(f"    → Likely interpretation: time field = number of F0 samples")


def main():
    print("Loading all English JSON files from:", BASE_DIR)
    entries, errors = load_all_english_json_files()
    print(f"Loaded {len(entries)} English entries from {len(set(fp for fp, _ in entries))} files")

    if errors:
        print(f"\nErrors loading {len(errors)} files:")
        for fp, err in errors[:10]:
            print(f"  {fp}: {err}")

    # Show breakdown by subdirectory
    by_subdir = defaultdict(int)
    for fp, _ in entries:
        subdir = fp.split("/")[0] if "/" in fp else "root"
        by_subdir[subdir] += 1
    print(f"\nBreakdown by subdirectory:")
    for subdir, count in sorted(by_subdir.items()):
        print(f"  {subdir}: {count} entries")

    analyze_phonemes(entries)
    analyze_note_types(entries)
    analyze_durations(entries)
    analyze_pitch(entries)
    analyze_f0(entries)
    analyze_structure(entries)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

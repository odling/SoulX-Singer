"""
Download English metadata (JSONL annotations) from the SoulX-Singer-Eval-Dataset
and save them as individual JSON files under the example-metadata/ folder.
"""

import os
import json
from huggingface_hub import hf_hub_download

REPO_ID = "Soul-AILab/SoulX-Singer-Eval-Dataset"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "example-metadata")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All annotation JSONL files in the repo
ANNOTATION_FILES = [
    "soulx-singer-eval/annotation/soulxsinger_eval.phone.prompt.jsonl",
    "soulx-singer-eval/annotation/soulxsinger_eval.phone.target.jsonl",
    "soulx-singer-eval/annotation/soulxsinger_eval.word.prompt.jsonl",
    "soulx-singer-eval/annotation/soulxsinger_eval.word.target.jsonl",
    "gmo-svs/annotation/opensource_eval.phone.prompt.jsonl",
    "gmo-svs/annotation/opensource_eval.phone.target.jsonl",
    "gmo-svs/annotation/opensource_eval.word.prompt.jsonl",
    "gmo-svs/annotation/opensource_eval.word.target.jsonl",
]

saved_count = 0
seen_items = set()

for annotation_file in ANNOTATION_FILES:
    print(f"\nProcessing: {annotation_file}")
    local_path = hf_hub_download(REPO_ID, annotation_file, repo_type="dataset")

    # Determine sub-folder from file name (e.g. "soulxsinger_eval.phone.target")
    base_name = os.path.basename(annotation_file).replace(".jsonl", "")

    sub_dir = os.path.join(OUTPUT_DIR, base_name)
    os.makedirs(sub_dir, exist_ok=True)

    en_count = 0
    total_count = 0

    with open(local_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total_count += 1
            entry = json.loads(line)

            # Filter for English only
            language = entry.get("language", "")
            if language.lower() not in ("english", "en"):
                continue

            en_count += 1

            # Use item_name as filename
            item_name = entry.get("item_name", f"entry_{en_count:04d}")
            # Replace characters that are problematic in filenames
            safe_name = item_name.replace("/", "_").replace("\\", "_")
            filename = f"{safe_name}.json"
            filepath = os.path.join(sub_dir, filename)

            with open(filepath, "w", encoding="utf-8") as out_f:
                json.dump(entry, out_f, indent=2, ensure_ascii=False)

            saved_count += 1

    print(f"  Total: {total_count}, English: {en_count}")

print(f"\n{'='*60}")
print(f"Done! Saved {saved_count} English metadata JSON files to {OUTPUT_DIR}/")
print(f"{'='*60}")

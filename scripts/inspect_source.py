from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def decode_csv(path: Path) -> tuple[str, list[str], list[dict[str, str]], int]:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                sample = []
                row_count = 0
                for row in reader:
                    row_count += 1
                    if len(sample) < 5:
                        sample.append({k: v for k, v in row.items() if k})
                return encoding, reader.fieldnames or [], sample, row_count
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"Could not decode {path}")


def inspect(raw_dir: Path, source_name: str) -> dict[str, object]:
    source_path = raw_dir / source_name
    encoding, columns, sample, row_count = decode_csv(source_path)
    files = [
        {"name": path.name, "bytes": path.stat().st_size}
        for path in sorted(raw_dir.glob("*"))
        if path.is_file()
    ]
    duplicate_columns = [name for name, count in Counter(columns).items() if name and count > 1]
    return {
        "source_file": str(source_path),
        "encoding": encoding,
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "duplicate_columns": duplicate_columns,
        "raw_files": files,
        "sample_rows": sample,
        "public_exclusions": ["Name", "Investigator or Source", "pdf", "href formula", "href", "private notes", "exact addresses"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect raw shark attack source files.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--source", default="attacks.csv")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = inspect(args.raw_dir, args.source)
    payload = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()


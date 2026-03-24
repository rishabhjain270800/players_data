import argparse
import os
import re
from typing import Iterable, Optional

import pandas as pd
import pyarrow.parquet as pq


def iter_parquet_files(root: str, pattern: Optional[str]) -> Iterable[str]:
    """
    Walk `root` and yield candidate parquet file paths.

    Parquet files in this dataset may not have a `.parquet` extension, so this
    function primarily relies on a filename pattern (e.g. `*.nakama-0`).
    """
    if pattern is None:
        # Sensible default for this dataset: filenames often end with `.nakama-0`
        pattern = "*.nakama-0*"

    # We only use simple suffix/name matching to avoid pulling in glob logic.
    # If you need complex matching, pass `--pattern`.
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name is None:
                continue
            if _matches_pattern(name, pattern):
                yield os.path.join(dirpath, name)


def _matches_pattern(filename: str, pattern: str) -> bool:
    """
    Very small glob-like matcher supporting:
    - leading/trailing `*`
    - exact match
    """
    if pattern == "*":
        return True
    if pattern.startswith("*") and pattern.endswith("*"):
        needle = pattern.strip("*")
        return needle in filename
    if pattern.startswith("*"):
        suffix = pattern[1:]
        return filename.endswith(suffix)
    if pattern.endswith("*"):
        prefix = pattern[:-1]
        return filename.startswith(prefix)
    return filename == pattern


def decode_event_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Decode the parquet `event` column (stored as bytes) into a readable string.
    """

    def decode_cell(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if isinstance(v, (bytes, bytearray)):
            return bytes(v).decode("utf-8", errors="replace")
        # If some files already contain strings, keep as-is.
        return v

    if "event" in df.columns:
        df["event"] = df["event"].apply(decode_cell)
    else:
        raise KeyError("Expected an 'event' column but none was found.")
    return df


def append_parquet_files_to_csv(
    input_root: str,
    output_csv: str,
    pattern: Optional[str],
) -> None:
    first = True

    # Ensure output directory exists.
    out_dir = os.path.dirname(os.path.abspath(output_csv))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    parquet_files = list(iter_parquet_files(input_root, pattern))
    if not parquet_files:
        raise FileNotFoundError(
            f"No parquet files found under {input_root!r} matching pattern {pattern!r}."
        )

    for path in parquet_files:
        table = pq.read_table(path)
        df = table.to_pandas()
        df = decode_event_column(df)

        # Extract exact calendar date from folder structure
        match = re.search(r'February_(\d+)', path)
        if match:
            day = match.group(1).zfill(2)
            df['date'] = f"2026-02-{day}"
        else:
            df['date'] = "Unknown"

        # Write header once, then append.
        df.to_csv(
            output_csv,
            mode="w" if first else "a",
            header=first,
            index=False,
            encoding="utf-8-sig",  # better default for Excel
        )
        first = False

    if first:
        raise RuntimeError("No files were processed; output CSV was not created.")


def main():
    parser = argparse.ArgumentParser(
        description="Read all parquet files in a folder, decode `event`, and write one CSV for Excel."
    )
    parser.add_argument(
        "input_folder",
        help="Folder containing parquet files (event column is binary/bytes).",
    )
    parser.add_argument(
        "output_csv",
        help="Output CSV path (will be UTF-8 with BOM for Excel compatibility).",
    )
    parser.add_argument(
        "--pattern",
        default="*.nakama-0*",
        help="Filename pattern used to find parquet files (default: '*.nakama-0*').",
    )
    args = parser.parse_args()

    append_parquet_files_to_csv(
        input_root=args.input_folder,
        output_csv=args.output_csv,
        pattern=args.pattern,
    )


if __name__ == "__main__":
    main()


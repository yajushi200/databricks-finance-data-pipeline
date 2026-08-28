"""Slice the PaySim dataset into daily CSV batch files.

PaySim's `step` column is one hour of simulated time (1-744 = 31 days).
This script maps each step to a calendar date and writes one CSV per day:

    data/landing/date=2026-06-01/transactions.csv
    data/landing/date=2026-06-02/transactions.csv
    ...

That turns one static Kaggle file into daily "arrivals" — the shape a real
pipeline ingests. Streams the file row by row, so memory use is tiny.

Usage:
    python scripts/slice_paysim.py                       # all 31 days
    python scripts/slice_paysim.py --start-day 1 --end-day 10
    python scripts/slice_paysim.py --input paysim.csv --out data/landing
"""

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path

BASE_DATE = date(2026, 6, 1)  # simulated day 1 = June 1, 2026


def step_to_day(step: int) -> int:
    """PaySim step (1-744, one per hour) -> simulated day number (1-31)."""
    return (step - 1) // 24 + 1


def day_to_date(day: int) -> date:
    return BASE_DATE + timedelta(days=day - 1)


def slice_file(input_path: Path, out_dir: Path, start_day: int, end_day: int) -> dict:
    """Split PaySim into one CSV per simulated day. Returns rows-per-day counts."""
    writers: dict[int, tuple] = {}  # day -> (file handle, csv writer)
    counts: dict[int, int] = {}

    with input_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        step_idx = header.index("step")

        for row in reader:
            day = step_to_day(int(row[step_idx]))
            if not (start_day <= day <= end_day):
                continue
            if day not in writers:
                day_dir = out_dir / f"date={day_to_date(day).isoformat()}"
                day_dir.mkdir(parents=True, exist_ok=True)
                handle = (day_dir / "transactions.csv").open(
                    "w", newline="", encoding="utf-8"
                )
                writer = csv.writer(handle)
                writer.writerow(header)
                writers[day] = (handle, writer)
                counts[day] = 0
            writers[day][1].writerow(row)
            counts[day] += 1

    for handle, _ in writers.values():
        handle.close()

    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="paysim.csv", help="path to the PaySim CSV")
    ap.add_argument("--out", default="data/landing", help="output directory")
    ap.add_argument("--start-day", type=int, default=1, help="first simulated day (1-31)")
    ap.add_argument("--end-day", type=int, default=31, help="last simulated day (1-31)")
    args = ap.parse_args()

    counts = slice_file(Path(args.input), Path(args.out), args.start_day, args.end_day)

    total = sum(counts.values())
    for day in sorted(counts):
        print(f"  {day_to_date(day).isoformat()}  {counts[day]:>9,} rows")
    print(f"Total: {total:,} rows across {len(counts)} daily files in {args.out}/")


if __name__ == "__main__":
    main()

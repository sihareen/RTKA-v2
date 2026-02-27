#!/usr/bin/env python3
"""
Bab 21.3: Export Attendance Report
==================================
Ekspor data absensi dari SQLite ke CSV.
"""

import argparse
import csv
import os
import sqlite3
from datetime import datetime

import attendance_utils as utils


def parse_args():
    parser = argparse.ArgumentParser(description="Export attendance report")
    parser.add_argument("--date", type=str, help="Tanggal spesifik (YYYY-MM-DD)")
    parser.add_argument("--from-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", type=str, help="End date (YYYY-MM-DD)")
    return parser.parse_args()


def validate_date(date_string):
    datetime.strptime(date_string, "%Y-%m-%d")
    return date_string


def resolve_range(args):
    if args.date:
        date_str = validate_date(args.date)
        return date_str, date_str

    if args.from_date and args.to_date:
        return validate_date(args.from_date), validate_date(args.to_date)

    today = datetime.now().strftime("%Y-%m-%d")
    return today, today


def main():
    args = parse_args()

    print("=" * 60)
    print("Face Attendance - Export Report")
    print("=" * 60)

    utils.ensure_directories()
    utils.init_database()

    try:
        from_date, to_date = resolve_range(args)
    except ValueError:
        print("Format tanggal salah. Gunakan YYYY-MM-DD.")
        return

    conn = sqlite3.connect(utils.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT person_code, person_name, event_date, event_time, confidence
        FROM attendance
        WHERE event_date BETWEEN ? AND ?
        ORDER BY event_date ASC, event_time ASC
        """,
        (from_date, to_date),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"Tidak ada data absensi untuk rentang {from_date} s/d {to_date}.")
        return

    output_name = f"attendance_report_{from_date}_to_{to_date}.csv"
    output_path = os.path.join(utils.EXPORT_DIR, output_name)

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["person_code", "person_name", "event_date", "event_time", "confidence"])
        for row in rows:
            writer.writerow(
                [
                    row["person_code"],
                    row["person_name"],
                    row["event_date"],
                    row["event_time"],
                    f"{row['confidence']:.2f}",
                ]
            )

    unique_people = len(set((row["person_code"] for row in rows)))
    print(f"Range          : {from_date} s/d {to_date}")
    print(f"Total records  : {len(rows)}")
    print(f"Unique persons : {unique_people}")
    print(f"CSV output     : {output_path}")


if __name__ == "__main__":
    main()

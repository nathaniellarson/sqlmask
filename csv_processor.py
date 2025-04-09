#!/usr/bin/env python3
"""
SQL Masker CSV Processor

This script processes a CSV file containing SQL queries, masks them using sqlmask
with a consistent mapping across all queries, and outputs:
1. A new CSV with an additional column containing masked SQL
2. A JSON file with the mapping used for masking

Usage:
    python csv_processor.py input.csv output.csv mapping.json --sql-column "query" --masked-column "masked_query"
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the parent directory to the path so we can import sqlmask
sys.path.insert(0, str(Path(__file__).parent.absolute()))
from sqlmask import SQLMasker


def process_csv(
    input_file: str,
    output_file: str,
    mapping_file: str,
    sql_column: str,
    masked_column: str,
    delimiter: str = ",",
    quotechar: str = '"',
    encoding: str = "utf-8"
) -> None:
    """
    Process a CSV file containing SQL queries, mask them, and output results.

    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file
        mapping_file: Path to the output mapping JSON file
        sql_column: Name of the column containing SQL queries
        masked_column: Name of the column to add with masked SQL
        delimiter: CSV delimiter character
        quotechar: CSV quote character
        encoding: File encoding
    """
    # Create a SQLMasker instance to maintain consistent mapping
    masker = SQLMasker()
    
    # First pass: read all rows and headers
    with open(input_file, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
        
        # Validate that the SQL column exists
        if sql_column not in reader.fieldnames:
            raise ValueError(f"SQL column '{sql_column}' not found in CSV. Available columns: {reader.fieldnames}")
        
        # Create a new fieldnames list with the masked column
        fieldnames = list(reader.fieldnames)
        if masked_column not in fieldnames:
            fieldnames.append(masked_column)
        
        # Read all rows
        rows = list(reader)
    
    # Process all SQL queries with the same masker instance
    for row in rows:
        sql_query = row[sql_column]
        if sql_query and sql_query.strip():
            masked_sql, _ = masker.encode(sql_query)
            row[masked_column] = masked_sql
        else:
            row[masked_column] = ""
    
    # Write the output CSV with the masked SQL
    with open(output_file, 'w', encoding=encoding, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter, quotechar=quotechar)
        writer.writeheader()
        writer.writerows(rows)
    
    # Write the mapping to a JSON file
    with open(mapping_file, 'w', encoding=encoding) as f:
        json.dump(masker._mapping, f, indent=2)
    
    print(f"Processed {len(rows)} rows")
    print(f"Output CSV written to: {output_file}")
    print(f"Mapping JSON written to: {mapping_file}")
    print(f"Mapping contains {len(masker._mapping)} entries")


def main() -> None:
    """Parse command line arguments and process the CSV file."""
    parser = argparse.ArgumentParser(description="Process SQL queries in a CSV file using sqlmask")
    parser.add_argument("input_file", help="Input CSV file containing SQL queries")
    parser.add_argument("output_file", help="Output CSV file with masked SQL")
    parser.add_argument("mapping_file", help="Output JSON file for the mapping")
    parser.add_argument("--sql-column", required=True, help="Name of the column containing SQL queries")
    parser.add_argument("--masked-column", default="masked_query", help="Name of the column to add with masked SQL")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter character")
    parser.add_argument("--quotechar", default='"', help="CSV quote character")
    parser.add_argument("--encoding", default="utf-8", help="File encoding")
    
    args = parser.parse_args()
    
    try:
        process_csv(
            args.input_file,
            args.output_file,
            args.mapping_file,
            args.sql_column,
            args.masked_column,
            args.delimiter,
            args.quotechar,
            args.encoding
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

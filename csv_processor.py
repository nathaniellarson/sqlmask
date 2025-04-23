#!/usr/bin/env python3
"""
CSV Processor for SQL masking and unmasking.

This script provides functionality to mask and unmask SQL queries in CSV files.
"""

import argparse
import csv
import json
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add the parent directory to the path so we can import sqlmask if needed
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from sqlmask.masker import SQLMasker
from sqlmask.unmasker import SQLUnmasker


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


def unmask_csv(
    input_file: str,
    output_file: str,
    mapping_file: str,
    masked_column: str,
    unmasked_column: str,
    delimiter: str = ",",
    quotechar: str = '"',
    encoding: str = "utf-8"
) -> None:
    """
    Process a CSV file and unmask SQL queries using a mapping file.

    Args:
        input_file: Path to the input CSV file containing masked SQL queries
        output_file: Path to the output CSV file
        mapping_file: Path to the input mapping JSON file
        masked_column: Name of the column containing masked SQL queries
        unmasked_column: Name of the column to write unmasked SQL queries to
        delimiter: CSV delimiter character
        quotechar: CSV quote character
        encoding: File encoding
    """
    # Create an unmasker with the mapping file
    unmasker = SQLUnmasker(mapping_file)
    
    # Read all rows and headers
    with open(input_file, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        rows = list(reader)
    
    if not fieldnames:
        raise ValueError("Input CSV file has no headers")
    
    if masked_column not in fieldnames:
        raise ValueError(f"Masked column '{masked_column}' not found in CSV headers")
    
    # Add the unmasked column to the fieldnames if it doesn't exist
    if unmasked_column not in fieldnames:
        fieldnames.append(unmasked_column)
    
    # Process all rows and unmask the SQL queries
    for row in rows:
        masked_sql = row[masked_column]
        if not masked_sql:
            row[unmasked_column] = ""
            continue
        
        # Unmask the SQL query using the SQLUnmasker
        row[unmasked_column] = unmasker.unmask(masked_sql)
    
    # Write the output CSV with unmasked SQL queries
    with open(output_file, 'w', encoding=encoding, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter, quotechar=quotechar)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Processed {len(rows)} rows with {len(fieldnames)} columns")
    print(f"Output CSV written to: {output_file}")
    print(f"Used mapping from: {mapping_file}")
    print(f"Mapping contains {len(unmasker.mapping)} entries")


def unmask_all_columns(
    input_file: str,
    output_file: str,
    mapping_file: str,
    delimiter: str = ",",
    quotechar: str = '"',
    encoding: str = "utf-8"
) -> None:
    """
    Process a CSV file and unmask all column values using a mapping file.
    The output CSV will have the same column names, but all masked values will be replaced with their original values.
    This function also handles masked values embedded within strings.

    Args:
        input_file: Path to the input CSV file containing masked values
        output_file: Path to the output CSV file
        mapping_file: Path to the input mapping JSON file
        delimiter: CSV delimiter character
        quotechar: CSV quote character
        encoding: File encoding
    """
    # Create an unmasker with the mapping file
    unmasker = SQLUnmasker(mapping_file)
    
    # Read all rows and headers
    with open(input_file, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        rows = list(reader)
    
    if not fieldnames:
        raise ValueError("Input CSV file has no headers")
    
    # Process all rows and unmask all values
    unmasked_rows = []
    for row in rows:
        unmasked_row = {}
        for column in fieldnames:
            value = row[column]
            unmasked_row[column] = unmasker.unmask(value)
        unmasked_rows.append(unmasked_row)
    
    # Write the output CSV with unmasked values
    with open(output_file, 'w', encoding=encoding, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter, quotechar=quotechar)
        writer.writeheader()
        writer.writerows(unmasked_rows)
    
    print(f"Processed {len(rows)} rows with {len(fieldnames)} columns")
    print(f"Output CSV written to: {output_file}")
    print(f"Used mapping from: {mapping_file}")
    print(f"Mapping contains {len(unmasker.mapping)} entries")


def mask_comments_only(
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
    Process a CSV file containing SQL queries, mask only the comments, and output results.
    This function preserves all SQL code and only obfuscates comments.

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
    
    # Process all SQL queries with the same masker instance, but only mask comments
    for row in rows:
        sql_query = row[sql_column]
        if sql_query and sql_query.strip():
            masked_sql, _ = masker.encode_comments_only(sql_query)
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
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Mask command
    mask_parser = subparsers.add_parser("mask", help="Mask SQL queries in a CSV file")
    mask_parser.add_argument("input_file", help="Input CSV file containing SQL queries")
    mask_parser.add_argument("output_file", help="Output CSV file with masked SQL")
    mask_parser.add_argument("mapping_file", help="Output JSON file for the mapping")
    mask_parser.add_argument("--sql-column", required=True, help="Name of the column containing SQL queries")
    mask_parser.add_argument("--masked-column", default="masked_query", help="Name of the column to add with masked SQL")
    mask_parser.add_argument("--delimiter", default=",", help="CSV delimiter character")
    mask_parser.add_argument("--quotechar", default='"', help="CSV quote character")
    mask_parser.add_argument("--encoding", default="utf-8", help="File encoding")
    
    # Mask Comments Only command
    mask_comments_parser = subparsers.add_parser("mask-comments", help="Mask only comments in SQL queries in a CSV file")
    mask_comments_parser.add_argument("input_file", help="Input CSV file containing SQL queries")
    mask_comments_parser.add_argument("output_file", help="Output CSV file with masked SQL comments")
    mask_comments_parser.add_argument("mapping_file", help="Output JSON file for the mapping")
    mask_comments_parser.add_argument("--sql-column", required=True, help="Name of the column containing SQL queries")
    mask_comments_parser.add_argument("--masked-column", default="masked_query", help="Name of the column to add with masked SQL")
    mask_comments_parser.add_argument("--delimiter", default=",", help="CSV delimiter character")
    mask_comments_parser.add_argument("--quotechar", default='"', help="CSV quote character")
    mask_comments_parser.add_argument("--encoding", default="utf-8", help="File encoding")
    
    # Unmask command
    unmask_parser = subparsers.add_parser("unmask", help="Unmask SQL queries in a CSV file")
    unmask_parser.add_argument("input_file", help="Input CSV file containing masked SQL queries")
    unmask_parser.add_argument("output_file", help="Output CSV file with unmasked SQL")
    unmask_parser.add_argument("mapping_file", help="Input JSON file with the mapping")
    unmask_parser.add_argument("--masked-column", required=True, help="Name of the column containing masked SQL queries")
    unmask_parser.add_argument("--unmasked-column", default="unmasked_query", help="Name of the column to add with unmasked SQL")
    unmask_parser.add_argument("--delimiter", default=",", help="CSV delimiter character")
    unmask_parser.add_argument("--quotechar", default='"', help="CSV quote character")
    unmask_parser.add_argument("--encoding", default="utf-8", help="File encoding")
    
    # Unmask All command
    unmask_all_parser = subparsers.add_parser("unmask-all", help="Unmask all columns in a CSV file using a mapping")
    unmask_all_parser.add_argument("input_file", help="Input CSV file containing masked values")
    unmask_all_parser.add_argument("output_file", help="Output CSV file with unmasked values")
    unmask_all_parser.add_argument("mapping_file", help="Input JSON file with the mapping")
    unmask_all_parser.add_argument("--delimiter", default=",", help="CSV delimiter character")
    unmask_all_parser.add_argument("--quotechar", default='"', help="CSV quote character")
    unmask_all_parser.add_argument("--encoding", default="utf-8", help="File encoding")
    
    # For backward compatibility, if no command is specified, default to mask
    args = parser.parse_args()
    
    try:
        if not args.command or args.command == "mask":
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
        elif args.command == "mask-comments":
            mask_comments_only(
                args.input_file,
                args.output_file,
                args.mapping_file,
                args.sql_column,
                args.masked_column,
                args.delimiter,
                args.quotechar,
                args.encoding
            )
        elif args.command == "unmask":
            unmask_csv(
                args.input_file,
                args.output_file,
                args.mapping_file,
                args.masked_column,
                args.unmasked_column,
                args.delimiter,
                args.quotechar,
                args.encoding
            )
        elif args.command == "unmask-all":
            unmask_all_columns(
                args.input_file,
                args.output_file,
                args.mapping_file,
                args.delimiter,
                args.quotechar,
                args.encoding
            )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

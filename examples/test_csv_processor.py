#!/usr/bin/env python3
"""
Test script for the SQL Masker CSV Processor

This script demonstrates how to use the CSV processor with a sample CSV file.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the csv_processor
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from csv_processor import process_csv


def main() -> None:
    """Run a test of the CSV processor with the sample CSV file."""
    # Define file paths
    current_dir = Path(__file__).parent
    input_file = current_dir / "sample_queries.csv"
    output_file = current_dir / "masked_queries.csv"
    mapping_file = current_dir / "query_mapping.json"
    
    # Process the sample CSV
    process_csv(
        input_file=str(input_file),
        output_file=str(output_file),
        mapping_file=str(mapping_file),
        sql_column="query",
        masked_column="masked_query"
    )
    
    print("\nTest completed successfully!")
    print(f"Check {output_file} for the masked queries")
    print(f"Check {mapping_file} for the mapping used")


if __name__ == "__main__":
    main()

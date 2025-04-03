#!/usr/bin/env python3
"""
SQL Masker - Encoding Script

This script takes an input SQL file, masks the identifiers, and writes the masked SQL
to an output file along with a mapping file that can be used for decoding.

Usage:
    python encode_sql.py input.sql output.sql [mapping.json]

If mapping.json is not provided, it will be created as output.sql.map.json
"""

import sys
import os
import json
from sqlmask.masker import SQLMasker


def encode_sql_file(input_path, output_path, mapping_path=None):
    """
    Encode a SQL file and save the masked SQL and mapping.
    
    Args:
        input_path: Path to the input SQL file
        output_path: Path to save the masked SQL
        mapping_path: Path to save the mapping (if None, uses output_path + '.map.json')
    """
    # Determine mapping path if not provided
    if mapping_path is None:
        mapping_path = f"{output_path}.map.json"
    
    # Read input SQL
    try:
        with open(input_path, 'r') as f:
            sql = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        return False
    
    # Mask the SQL
    try:
        masker = SQLMasker()
        masked_sql, mapping = masker.encode(sql)
    except Exception as e:
        print(f"Error masking SQL: {e}")
        return False
    
    # Write masked SQL to output file
    try:
        with open(output_path, 'w') as f:
            f.write(masked_sql)
    except Exception as e:
        print(f"Error writing output file: {e}")
        return False
    
    # Write mapping to mapping file
    try:
        with open(mapping_path, 'w') as f:
            json.dump(mapping, f, indent=2)
    except Exception as e:
        print(f"Error writing mapping file: {e}")
        return False
    
    print(f"Successfully masked SQL from {input_path}")
    print(f"Masked SQL written to {output_path}")
    print(f"Mapping written to {mapping_path}")
    return True


if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input.sql output.sql [mapping.json]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    mapping_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Validate input file exists
    if not os.path.isfile(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Encode the SQL file
    success = encode_sql_file(input_path, output_path, mapping_path)
    sys.exit(0 if success else 1)

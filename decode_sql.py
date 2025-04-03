#!/usr/bin/env python3
"""
SQL Masker - Decoding Script

This script takes a masked SQL file and a mapping file, decodes the SQL,
and writes the original SQL to an output file.

Usage:
    python decode_sql.py masked.sql mapping.json output.sql
"""

import sys
import os
import json
from typing import Dict, Any, Optional, Union, cast
from sqlmask.masker import SQLMasker


def decode_sql_file(input_path: str, mapping_path: str, output_path: str) -> bool:
    """
    Decode a masked SQL file using the provided mapping.
    
    Args:
        input_path: Path to the masked SQL file
        mapping_path: Path to the mapping file
        output_path: Path to save the decoded SQL
        
    Returns:
        bool: True if decoding was successful, False otherwise
    """
    # Read masked SQL
    try:
        with open(input_path, 'r') as f:
            masked_sql: str = f.read()
    except Exception as e:
        print(f"Error reading masked SQL file: {e}")
        return False
    
    # Read mapping
    try:
        with open(mapping_path, 'r') as f:
            mapping: Dict[str, str] = cast(Dict[str, str], json.load(f))
    except Exception as e:
        print(f"Error reading mapping file: {e}")
        return False
    
    # Decode the SQL
    try:
        masker = SQLMasker()
        decoded_sql: str = masker.decode(masked_sql, mapping)
    except Exception as e:
        print(f"Error decoding SQL: {e}")
        return False
    
    # Write decoded SQL to output file
    try:
        with open(output_path, 'w') as f:
            f.write(decoded_sql)
    except Exception as e:
        print(f"Error writing output file: {e}")
        return False
    
    print(f"Successfully decoded SQL from {input_path}")
    print(f"Decoded SQL written to {output_path}")
    return True


if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} masked.sql mapping.json output.sql")
        sys.exit(1)
    
    input_path: str = sys.argv[1]
    mapping_path: str = sys.argv[2]
    output_path: str = sys.argv[3]
    
    # Validate input files exist
    if not os.path.isfile(input_path):
        print(f"Masked SQL file not found: {input_path}")
        sys.exit(1)
    
    if not os.path.isfile(mapping_path):
        print(f"Mapping file not found: {mapping_path}")
        sys.exit(1)
    
    # Decode the SQL file
    success: bool = decode_sql_file(input_path, mapping_path, output_path)
    sys.exit(0 if success else 1)

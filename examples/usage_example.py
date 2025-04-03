#!/usr/bin/env python3
"""
SQL Masker - Usage Example

This script demonstrates how to use the SQLMasker class directly in Python code
to encode and decode SQL statements.
"""

import os
import sys
import json

# Add the parent directory to the path so we can import sqlmask
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlmask.masker import SQLMasker


def main():
    # Sample SQL query with comments
    sql = """
    -- Query to get active users with their orders
    SELECT 
        u.user_id, 
        u.name, 
        u.email, /* User's email address */
        o.order_id, 
        o.total
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    WHERE u.status = 'active' -- Only active users
    AND o.created_at > '2025-01-01' /* Orders from 2025 onwards */
    ORDER BY o.total DESC
    LIMIT 10
    """
    
    print("Original SQL:")
    print(sql)
    print("\n" + "-" * 50 + "\n")
    
    # Create a masker instance
    masker = SQLMasker()
    
    # Encode the SQL
    masked_sql, mapping = masker.encode(sql)
    
    print("Masked SQL:")
    print(masked_sql)
    print("\n" + "-" * 50 + "\n")
    
    print("Mapping:")
    print(json.dumps(mapping, indent=2))
    print("\n" + "-" * 50 + "\n")
    
    # Decode the SQL
    decoded_sql = masker.decode(masked_sql, mapping)
    
    print("Decoded SQL:")
    print(decoded_sql)
    print("\n" + "-" * 50 + "\n")
    
    # Verify the decoded SQL matches the original
    if decoded_sql == sql:
        print("✅ Success! The decoded SQL matches the original.")
    else:
        print("❌ Error! The decoded SQL does not match the original.")
        
    # Demonstrate repeated string masking
    print("\nDemonstrating repeated string masking:")
    repeated_sql = """
    SELECT * FROM users WHERE status = 'active' OR role = 'active'
    """
    print("\nOriginal SQL with repeated strings:")
    print(repeated_sql)
    
    masked_repeated, repeated_mapping = masker.encode(repeated_sql)
    print("\nMasked SQL:")
    print(masked_repeated)
    
    print("\nMapping:")
    print(json.dumps(repeated_mapping, indent=2))
    
    decoded_repeated = masker.decode(masked_repeated, repeated_mapping)
    print("\nDecoded SQL:")
    print(decoded_repeated)
    
    if decoded_repeated == repeated_sql:
        print("\n✅ Success! The decoded SQL with repeated strings matches the original.")
    else:
        print("\n❌ Error! The decoded SQL with repeated strings does not match the original.")


if __name__ == "__main__":
    main()

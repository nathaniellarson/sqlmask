# SQLMask

SQLMask is a Python package that allows you to obfuscate SQL statements while preserving their structure. It's useful for sharing SQL queries without exposing sensitive column names, table names, or aliases.

## Features

- Encode: Obfuscate column names, table names, and aliases in SQL statements
- Decode: Restore original names from obfuscated SQL statements
- Preserves SQL structure including joins, selects, inserts, and all keywords
- Maintains mapping between original and obfuscated names

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command-line Scripts

SQLMask provides two command-line scripts for encoding and decoding SQL files:

#### Encoding SQL

```bash
python encode_sql.py input.sql output.sql [mapping.json]
```

If `mapping.json` is not provided, it will be created as `output.sql.map.json`.

#### Decoding SQL

```bash
python decode_sql.py masked.sql mapping.json output.sql
```

### Python API

You can also use the SQLMasker class directly in your Python code:

```python
from sqlmask import SQLMasker

# Create a masker instance
masker = SQLMasker()

# Obfuscate a SQL statement
sql = "SELECT user_id, email FROM users WHERE status = 'active'"
masked_sql, mapping = masker.encode(sql)

# Decode back to original
original_sql = masker.decode(masked_sql, mapping)
```

## Examples

Check out the `examples` directory for sample SQL files and usage examples:

- `example.sql`: A sample SQL query with various features
- `usage_example.py`: A Python script demonstrating how to use the SQLMasker class
- `sample_queries.csv`: A sample CSV file containing SQL queries for processing
- `test_csv_processor.py`: A script demonstrating how to use the CSV processor

To run the example:

```bash
python examples/usage_example.py
```

Or to encode and decode the example SQL file:

```bash
python encode_sql.py examples/example.sql examples/masked.sql examples/mapping.json
python decode_sql.py examples/masked.sql examples/mapping.json examples/decoded.sql
```

## CSV Processing

The package includes a CSV processor script that can be used to mask and unmask SQL queries in CSV files.

### Masking SQL Queries

```bash
python csv_processor.py mask input.csv output.csv mapping.json --sql-column="query"
```

This will:
1. Read all rows from input.csv
2. For each row, mask the SQL query in the "query" column
3. Add a new column "masked_query" with the masked SQL
4. Write the output to output.csv
5. Save the mapping to mapping.json

### Masking Only Comments in SQL Queries

```bash
python csv_processor.py mask-comments input.csv output.csv mapping.json --sql-column="query"
```

This will:
1. Read all rows from input.csv
2. For each row, mask ONLY the comments in the SQL query in the "query" column, leaving all code intact
3. Add a new column "masked_query" with the SQL that has masked comments
4. Write the output to output.csv
5. Save the mapping to mapping.json

#### Masking Arguments

- `input.csv`: Path to the input CSV file containing SQL queries
- `output.csv`: Path to the output CSV file with masked SQL
- `mapping.json`: Path to save the mapping JSON file
- `--sql-column`: Name of the column in the input CSV that contains SQL queries (required)
- `--masked-column`: Name of the column to add with masked SQL (default: masked_query)
- `--delimiter`: CSV delimiter character (default: ,)
- `--quotechar`: CSV quote character (default: ")
- `--encoding`: File encoding (default: utf-8)

#### Masking Example

```bash
python csv_processor.py mask examples/sample_queries.csv examples/masked_queries.csv examples/mapping.json --sql-column query --masked-column masked_query
```

This will:
1. Read SQL queries from the 'query' column in examples/sample_queries.csv
2. Process each query using SQLMasker with a consistent mapping
3. Create a new CSV file (examples/masked_queries.csv) with an additional 'masked_query' column
4. Save the mapping to examples/mapping.json

### Unmasking SQL Queries

```bash
python csv_processor.py unmask masked.csv unmasked.csv mapping.json --masked-column "masked_query"
```

#### Unmasking Arguments

- `masked.csv`: Path to the input CSV file containing masked SQL queries
- `unmasked.csv`: Path to the output CSV file with unmasked SQL
- `mapping.json`: Path to the mapping JSON file used for unmasking
- `--masked-column`: Name of the column containing masked SQL queries (required)
- `--unmasked-column`: Name of the column to add with unmasked SQL (default: unmasked_query)
- `--delimiter`: CSV delimiter character (default: ,)
- `--quotechar`: CSV quote character (default: ")
- `--encoding`: File encoding (default: utf-8)

#### Unmasking Example

```bash
python csv_processor.py unmask examples/masked_queries.csv examples/unmasked_queries.csv examples/mapping.json --masked-column masked_query
```

This will:
1. Read masked SQL queries from the 'masked_query' column in examples/masked_queries.csv
2. Load the mapping from examples/mapping.json
3. Unmask each query using the mapping
4. Create a new CSV file (examples/unmasked_queries.csv) with an additional 'unmasked_query' column

### Unmasking All Columns

For cases where you need to unmask all values in a CSV file:

```bash
python csv_processor.py unmask-all masked_data.csv unmasked_data.csv mapping.json
```

#### Unmask-All Arguments

- `masked_data.csv`: Path to the input CSV file containing masked values
- `unmasked_data.csv`: Path to the output CSV file with unmasked values
- `mapping.json`: Path to the mapping JSON file used for unmasking
- `--delimiter`: CSV delimiter character (default: ,)
- `--quotechar`: CSV quote character (default: ")
- `--encoding`: File encoding (default: utf-8)

#### Unmask-All Example

```bash
python csv_processor.py unmask-all examples/masked_data.csv examples/unmasked_data.csv examples/mapping.json
```

This will:
1. Read all columns and rows from examples/masked_data.csv
2. Load the mapping from examples/mapping.json
3. For each cell value, check if it exists in the mapping and replace it with the original value
4. Create a new CSV file (examples/unmasked_data.csv) with all values unmasked
5. The output CSV will have the same column names as the input CSV

## Running Tests

To run the tests for the SQLMask package:

```bash
# From the project root directory
python -m pytest sqlmask/tests/
```

Or if you have the package installed:

```bash
pytest sqlmask/tests/
```

## How It Works

SQLMask uses a simple regex-based approach to mask identifiers in SQL statements:

1. It preserves string literals exactly as they are
2. It replaces identifiers with unique placeholders (e.g., `m1`, `m2`, etc.)
3. It preserves SQL keywords and special characters
4. It maintains a mapping between original identifiers and their masked versions
5. It can optionally mask only comments while preserving all code

This allows you to:
- Obfuscate sensitive table and column names
- Mask only comments in code while preserving the actual SQL structure
- Share SQL queries without revealing schema details
- Decode masked SQL back to its original form when needed

## License

MIT

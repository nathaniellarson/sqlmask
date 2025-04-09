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

SQLMask provides a CSV processor that can mask SQL queries in a CSV file while maintaining consistent masking across all queries.

### Usage

```bash
python csv_processor.py input.csv output.csv mapping.json --sql-column SQL_COLUMN [--masked-column MASKED_COLUMN]
```

Parameters:
- `input.csv`: Path to the input CSV file containing SQL queries
- `output.csv`: Path to the output CSV file that will contain the original data plus masked SQL
- `mapping.json`: Path to save the mapping JSON file
- `--sql-column`: Name of the column in the input CSV that contains SQL queries (required)
- `--masked-column`: Name of the column to add with masked SQL (default: masked_query)
- `--delimiter`: CSV delimiter character (default: ,)
- `--quotechar`: CSV quote character (default: ")
- `--encoding`: File encoding (default: utf-8)

### Example

```bash
python csv_processor.py examples/sample_queries.csv examples/masked_queries.csv examples/mapping.json --sql-column query --masked-column masked_query
```

This will:
1. Read SQL queries from the 'query' column in examples/sample_queries.csv
2. Process each query using SQLMasker with a consistent mapping
3. Create a new CSV file (examples/masked_queries.csv) with an additional 'masked_query' column
4. Save the mapping to examples/masked_queries.csv.map.json

## Running Tests

```bash
pytest tests/
```

## How It Works

SQLMask uses a simple regex-based approach to mask identifiers in SQL statements:

1. It preserves string literals exactly as they are
2. It replaces identifiers with unique placeholders (e.g., `m1`, `m2`, etc.)
3. It preserves SQL keywords and special characters
4. It maintains a mapping between original identifiers and their masked versions

This allows you to:
- Obfuscate sensitive table and column names
- Share SQL queries without revealing schema details
- Decode masked SQL back to its original form when needed

## License

MIT

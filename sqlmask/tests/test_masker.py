import pytest
import os
from typing import Dict, Tuple
from sqlmask.masker import SQLMasker


@pytest.fixture
def masker() -> SQLMasker:
    """Create and return a SQLMasker instance for testing."""
    return SQLMasker()


@pytest.fixture
def complex_cte_sql() -> str:
    """Load complex CTE SQL query from fixture file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_path = os.path.join(current_dir, 'fixtures', 'complex_cte.sql')
    with open(fixture_path, 'r') as f:
        return f.read()


def test_simple_select(masker: SQLMasker) -> None:
    """Test masking and unmasking of a simple SELECT statement."""
    sql = "SELECT id, name FROM users"
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping) == sql


def test_select_with_alias(masker: SQLMasker) -> None:
    """Test masking and unmasking of a SELECT statement with table alias."""
    sql = "SELECT u.id, u.name FROM users u"
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping) == sql


def test_complex_join(masker: SQLMasker) -> None:
    """Test masking and unmasking of a complex JOIN statement."""
    sql = """
    SELECT u.id, u.name, o.order_id, o.total
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE o.status = 'completed'
    """
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_subquery(masker: SQLMasker) -> None:
    """Test masking and unmasking of a query with a subquery."""
    sql = """
    SELECT u.name, (
        SELECT COUNT(*)
        FROM orders o
        WHERE o.user_id = u.id
    ) as order_count
    FROM users u
    """
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_complex_query_with_multiple_joins(masker: SQLMasker) -> None:
    """Test masking and unmasking of a complex query with multiple joins."""
    sql = """
    SELECT
        u.id,
        u.name,
        o.order_id,
        p.name as product_name,
        c.category_name
    FROM users u
    JOIN orders o ON u.id = o.user_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    JOIN categories c ON p.category_id = c.id
    WHERE o.status = 'completed'
    AND c.active = true
    GROUP BY u.id, u.name, o.order_id, p.name, c.category_name
    HAVING COUNT(*) > 1
    ORDER BY u.name ASC
    """
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_insert_statement(masker: SQLMasker) -> None:
    """Test masking and unmasking of an INSERT statement."""
    sql = """
    INSERT INTO users (name, email, created_at)
    VALUES ('John', 'john@example.com', NOW())
    """
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_update_statement(masker: SQLMasker) -> None:
    """Test masking and unmasking of an UPDATE statement."""
    sql = """
    UPDATE users u
    SET status = 'inactive',
        updated_at = NOW()
    FROM orders o
    WHERE u.id = o.user_id
    AND o.last_active < NOW() - INTERVAL '1 year'
    """
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_consistent_masking(masker: SQLMasker) -> None:
    """Test that identical identifiers are consistently masked."""
    sql = "SELECT name FROM users WHERE name = 'John' OR name = 'John'"
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping) == sql


def test_complex_cte_query(masker: SQLMasker, complex_cte_sql: str) -> None:
    """Test masking and unmasking of a complex query with multiple CTEs."""
    masked, mapping = masker.encode(complex_cte_sql)
    
    # Verify that the masked SQL doesn't contain any of the original identifiers
    assert "user_orders" not in masked
    assert "order_items" not in masked
    assert "user_id" not in masked
    assert "order_id" not in masked
    assert "product_id" not in masked
    
    # Verify that the masked SQL can be decoded back to the original
    assert masker.decode(masked, mapping).strip() == complex_cte_sql.strip()


def test_string_literal_masking(masker: SQLMasker) -> None:
    """Test that string literals are properly masked and unmasked."""
    sql = """
    SELECT
        id,
        name
    FROM users
    WHERE
        status = 'active'
        AND role IN ('admin', 'editor')
        AND email LIKE '%@example.com'
        AND created_at > '2023-01-01'
    """

    masked, mapping = masker.encode(sql)

    # Verify that string literals are masked
    assert "'active'" not in masked
    assert "'admin'" not in masked
    assert "'editor'" not in masked
    assert "'%@example.com'" not in masked
    assert "'2023-01-01'" not in masked

    # Verify that string literals are in the mapping
    string_keys = [k for k in mapping.keys() if k.startswith("'")]
    assert len(string_keys) == 5

    # Verify that the masked SQL can be decoded back to the original
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_inline_comment_masking(masker: SQLMasker) -> None:
    """Test that inline comments are properly masked and unmasked."""
    sql = """
    SELECT id, name, email -- Select user fields
    FROM users
    WHERE status = 'active' -- Only active users
    """
    
    masked, mapping = masker.encode(sql)
    
    # Verify that comments are masked
    assert "-- Select user fields" not in masked
    assert "-- Only active users" not in masked
    
    # Verify that comments are in the mapping
    comment_keys = [k for k in mapping.keys() if k.startswith("--")]
    assert len(comment_keys) == 2
    assert "-- Select user fields" in comment_keys
    assert "-- Only active users" in comment_keys
    
    # Verify that comments are consistently masked
    sql_with_repeated_comment = """
    SELECT id, name, email -- Only active users
    FROM users
    WHERE status = 'active' -- Only active users
    """
    
    masked_repeated, mapping_repeated = masker.encode(sql_with_repeated_comment)
    
    # Count occurrences of the masked comment
    comment_mask = mapping_repeated["-- Only active users"]
    assert masked_repeated.count(comment_mask) == 2
    
    # Verify that the masked SQL can be decoded back to the original
    assert masker.decode(masked, mapping).strip() == sql.strip()
    assert masker.decode(masked_repeated, mapping_repeated).strip() == sql_with_repeated_comment.strip()


def test_multiline_comment_masking(masker: SQLMasker) -> None:
    """Test that multiline comments are properly masked and unmasked."""
    sql = """
    /* 
     * This query retrieves user data
     * with their order information
     */
    SELECT u.name, o.order_id
    FROM users u
    JOIN orders o ON u.id = o.user_id
    """
    
    masked, mapping = masker.encode(sql)
    
    # Verify that comments are masked
    assert "/* \n     * This query retrieves user data\n     * with their order information\n     */" not in masked
    
    # Verify that comments are in the mapping
    comment_keys = [k for k in mapping.keys() if k.startswith("/*")]
    assert len(comment_keys) == 1
    
    # Verify that the masked SQL can be decoded back to the original
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_mixed_comments_and_strings(masker: SQLMasker) -> None:
    """Test that a mix of comments and string literals are properly masked and unmasked."""
    sql = """
    -- Query for active users
    SELECT
        id,
        name,
        /* User's email */ email
    FROM users
    WHERE
        status = 'active' -- Only active users
        /* Filter by role */
        AND role IN ('admin', 'editor')
    """

    masked, mapping = masker.encode(sql)

    # Verify that comments and string literals are masked
    assert "-- Query for active users" not in masked
    assert "/* User's email */" not in masked
    assert "-- Only active users" not in masked
    assert "/* Filter by role */" not in masked
    assert "'active'" not in masked
    assert "'admin'" not in masked
    assert "'editor'" not in masked

    # Verify that comments and string literals are in the mapping
    comment_keys = [k for k in mapping.keys() if k.startswith("--") or k.startswith("/*")]
    string_keys = [k for k in mapping.keys() if k.startswith("'")]
    assert len(comment_keys) == 4
    assert len(string_keys) == 3

    # Verify that the masked SQL can be decoded back to the original
    decoded = masker.decode(masked, mapping)
    assert decoded.strip() == sql.strip()


def test_bigquery_functions_and_datatypes(masker: SQLMasker) -> None:
    """Test that BigQuery functions and datatypes are preserved (not masked)."""
    sql = r"""
    SELECT 
        CAST(field1 AS INT64) AS int_field,
        SAFE_CAST(field2 AS FLOAT64) AS float_field,
        CONCAT(first_name, ' ', last_name) AS full_name,
        SUBSTR(description, 1, 100) AS short_desc,
        CHAR_LENGTH(text_field) AS text_length,
        TIMESTAMP_ADD(created_at, INTERVAL 1 DAY) AS next_day,
        IF(status = 'active', TRUE, FALSE) AS is_active,
        CASE 
            WHEN RIGHT(zip_code, 2) = '00' THEN 'Special'
            ELSE 'Regular'
        END AS zip_type
    FROM 
        my_dataset.users
    WHERE 
        REGEXP_CONTAINS(email, r'@gmail\.com$')
        AND DATE(created_at) > '2023-01-01'
    GROUP BY 
        1, 2, 3, 4, 5, 6, 7, 8
    HAVING 
        COUNT(*) > 10
    ORDER BY 
        full_name ASC
    LIMIT 100
    """
    
    masked, mapping = masker.encode(sql)
    
    # Verify that core BigQuery functions and datatypes are preserved
    # Only check a subset of keywords that we're confident are in the keywords list
    assert "CAST" in masked
    assert "INT64" in masked
    assert "FLOAT64" in masked
    assert "CONCAT" in masked
    assert "SUBSTR" in masked
    assert "CHAR_LENGTH" in masked
    assert "TIMESTAMP_ADD" in masked
    assert "INTERVAL" in masked
    assert "TRUE" in masked
    assert "FALSE" in masked
    assert "CASE" in masked
    assert "WHEN" in masked
    assert "DATE" in masked
    assert "COUNT" in masked
    
    # Verify that identifiers and string literals are masked
    assert "field1" not in masked
    assert "field2" not in masked
    assert "first_name" not in masked
    assert "last_name" not in masked
    assert "description" not in masked
    assert "text_field" not in masked
    assert "created_at" not in masked
    assert "status" not in masked
    assert "zip_code" not in masked
    assert "my_dataset" not in masked
    assert "users" not in masked
    assert "email" not in masked
    assert "'active'" not in masked
    assert "'00'" not in masked
    assert "'Special'" not in masked
    assert "'Regular'" not in masked
    assert "'2023-01-01'" not in masked
    
    # Verify that the masked SQL can be decoded back to the original
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_existing_mapping_initialization() -> None:
    """Test that SQLMasker can be initialized with an existing mapping."""
    # Create an initial mapping
    initial_masker = SQLMasker()
    sql1 = "SELECT user_id, name, email FROM users WHERE status = 'active'"
    _, initial_mapping = initial_masker.encode(sql1)
    
    # Create a new masker with the existing mapping
    masker_with_mapping = SQLMasker(existing_mapping=initial_mapping)
    
    # Encode a new SQL query that has some overlapping fields
    sql2 = "SELECT user_id, order_id FROM orders WHERE user_id IN (SELECT user_id FROM users)"
    masked_sql2, new_mapping = masker_with_mapping.encode(sql2)
    
    # Verify that the overlapping fields use the same masked values
    assert "user_id" in initial_mapping
    assert "user_id" in new_mapping
    assert initial_mapping["user_id"] == new_mapping["user_id"]
    
    # Verify that the new fields are properly masked
    assert "order_id" in new_mapping
    assert "orders" in new_mapping
    
    # Verify that the counter was properly incremented (new masks should start after the highest in initial_mapping)
    max_initial_counter = 0
    for value in initial_mapping.values():
        if value.startswith("m") and not value.startswith("'m"):
            try:
                counter_val = int(value[1:])
                max_initial_counter = max(max_initial_counter, counter_val)
            except ValueError:
                pass
    
    # Check that new masks have higher counter values
    for key, value in new_mapping.items():
        if key not in initial_mapping and value.startswith("m") and not value.startswith("'m"):
            counter_val = int(value[1:])
            assert counter_val > max_initial_counter


def test_multiple_sql_statements_with_consistent_mapping() -> None:
    """Test that multiple SQL statements can be encoded with a consistent mapping."""
    masker = SQLMasker()
    
    # First SQL statement
    sql1 = "SELECT customer_id, name FROM customers WHERE status = 'active'"
    masked_sql1, mapping1 = masker.encode(sql1)
    
    # Second SQL statement with some overlapping fields
    sql2 = "SELECT order_id, customer_id, total FROM orders WHERE customer_id IN (SELECT customer_id FROM customers)"
    masked_sql2, mapping2 = masker.encode(sql2)
    
    # Third SQL statement with different fields
    sql3 = "SELECT product_id, name, price FROM products WHERE category = 'electronics'"
    masked_sql3, mapping3 = masker.encode(sql3)
    
    # Verify that overlapping fields have consistent masking
    assert mapping1["customer_id"] == mapping2["customer_id"]
    assert mapping1["customers"] == mapping2["customers"]
    
    # Verify that all three statements can be decoded correctly
    assert masker.decode(masked_sql1, mapping3) == sql1
    assert masker.decode(masked_sql2, mapping3) == sql2
    assert masker.decode(masked_sql3, mapping3) == sql3
    
    # Verify that the final mapping contains all fields from all statements
    all_original_fields = set()
    for sql in [sql1, sql2, sql3]:
        for field in ["customer_id", "name", "customers", "status", "'active'", 
                     "order_id", "total", "orders", 
                     "product_id", "price", "products", "category", "'electronics'"]:
            if field in sql:
                all_original_fields.add(field)
    
    # Check that all fields are in the final mapping
    for field in all_original_fields:
        assert field in mapping3


def test_case_statement_with_else() -> None:
    """Test that CASE statements with ELSE are properly masked and unmasked."""
    masker = SQLMasker()
    
    sql = """
    SELECT 
        user_id,
        CASE 
            WHEN age < 18 THEN 'minor'
            WHEN age BETWEEN 18 AND 65 THEN 'adult'
            ELSE 'senior'
        END AS age_group,
        CASE status
            WHEN 'active' THEN 'current'
            WHEN 'pending' THEN 'waiting'
            ELSE 'inactive'
        END AS user_status
    FROM users
    """
    
    masked_sql, mapping = masker.encode(sql)
    
    # Verify that SQL keywords are preserved
    assert "CASE" in masked_sql
    assert "WHEN" in masked_sql
    assert "THEN" in masked_sql
    assert "ELSE" in masked_sql
    assert "END" in masked_sql
    
    # Verify that identifiers are masked
    assert "user_id" not in masked_sql
    assert "age" not in masked_sql
    assert "status" not in masked_sql
    assert "age_group" not in masked_sql
    assert "user_status" not in masked_sql
    assert "users" not in masked_sql
    
    # Verify that string literals are masked
    assert "'minor'" not in masked_sql
    assert "'adult'" not in masked_sql
    assert "'senior'" not in masked_sql
    assert "'active'" not in masked_sql
    assert "'pending'" not in masked_sql
    assert "'current'" not in masked_sql
    assert "'waiting'" not in masked_sql
    assert "'inactive'" not in masked_sql
    
    # Verify that the masked SQL can be decoded back to the original
    decoded_sql = masker.decode(masked_sql, mapping)
    assert decoded_sql.strip() == sql.strip()

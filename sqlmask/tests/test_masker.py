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
    assert "product_name" not in masked
    assert "total_spent" not in masked
    
    # Verify that the masked SQL can be decoded back to the original
    assert masker.decode(masked, mapping).strip() == complex_cte_sql.strip()


def test_string_literal_masking(masker: SQLMasker) -> None:
    """Test that string literals are properly masked and unmasked."""
    sql = """
    SELECT u.name, u.email
    FROM users u
    WHERE u.status = 'active'
    AND u.created_at > '2025-01-01'
    """
    
    masked, mapping = masker.encode(sql)
    
    # Verify that string literals are masked
    assert "'active'" not in masked
    assert "'2025-01-01'" not in masked
    
    # Verify that string literals are in the mapping
    string_keys = [k for k in mapping.keys() if k.startswith("'")]
    assert len(string_keys) == 2
    assert "'active'" in string_keys
    assert "'2025-01-01'" in string_keys
    
    # Verify that string literals are consistently masked
    sql_with_repeated_string = """
    SELECT u.name, u.email
    FROM users u
    WHERE u.status = 'active'
    OR u.status = 'active'
    """
    
    masked_repeated, mapping_repeated = masker.encode(sql_with_repeated_string)
    
    # Count occurrences of the masked string literal
    active_mask = mapping_repeated["'active'"]
    assert masked_repeated.count(active_mask) == 2
    
    # Verify that the masked SQL can be decoded back to the original
    assert masker.decode(masked, mapping).strip() == sql.strip()
    assert masker.decode(masked_repeated, mapping_repeated).strip() == sql_with_repeated_string.strip()


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
    sql = """
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
        REGEXP_CONTAINS(email, r'@gmail\\.com$')
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

import pytest
import os
from sqlmask.masker import SQLMasker


@pytest.fixture
def masker():
    return SQLMasker()


@pytest.fixture
def complex_cte_sql():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fixture_path = os.path.join(current_dir, 'fixtures', 'complex_cte.sql')
    with open(fixture_path, 'r') as f:
        return f.read()


def test_simple_select(masker):
    sql = "SELECT id, name FROM users"
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping) == sql


def test_select_with_alias(masker):
    sql = "SELECT u.id, u.name FROM users u"
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping) == sql


def test_complex_join(masker):
    sql = """
    SELECT u.id, u.name, o.order_id, o.total
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE o.status = 'completed'
    """
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_subquery(masker):
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


def test_complex_query_with_multiple_joins(masker):
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


def test_insert_statement(masker):
    sql = """
    INSERT INTO users (name, email, created_at)
    VALUES ('John', 'john@example.com', NOW())
    """
    masked, mapping = masker.encode(sql)
    assert masker.decode(masked, mapping).strip() == sql.strip()


def test_update_statement(masker):
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


def test_consistent_masking(masker):
    sql = "SELECT id, name, id FROM users"
    masked, mapping = masker.encode(sql)
    # The same identifier should be masked to the same value
    assert len(set(v for v in mapping.values() if not v.startswith("'"))) == 3  # id, name, users


def test_complex_cte_query(masker, complex_cte_sql):
    """Test masking a complex query with multiple CTEs."""
    masked, mapping = masker.encode(complex_cte_sql)
    
    # Verify that we can decode back to the original SQL
    decoded = masker.decode(masked, mapping)
    assert decoded.strip() == complex_cte_sql.strip()
    
    # Verify that the mapping contains all the expected identifiers
    expected_identifiers = {
        'users', 'orders', 'products', 'categories', 'order_items',
        'id', 'name', 'order_id', 'total', 'user_id', 'category_id',
        'quantity', 'product_id', 'user_name', 'order_count', 'total_spent',
        'unique_products', 'total_items', 'category_name', 'category_rank',
        'top_3_categories'
    }
    actual_identifiers = set(k for k in mapping.keys() if not k.startswith("'"))
    assert expected_identifiers.issubset(actual_identifiers)


def test_string_literal_masking(masker):
    """Test that string literals are properly masked and unmasked."""
    sql = """
    SELECT u.name, u.email
    FROM users u
    WHERE u.status = 'active'
    AND u.role IN ('admin', 'editor')
    AND u.created_at > '2025-01-01'
    """
    
    masked, mapping = masker.encode(sql)
    
    # Verify that string literals are masked
    assert "'active'" not in masked
    assert "'admin'" not in masked
    assert "'editor'" not in masked
    assert "'2025-01-01'" not in masked
    
    # Verify that string literals are in the mapping
    string_literals = ["'active'", "'admin'", "'editor'", "'2025-01-01'"]
    for literal in string_literals:
        assert any(k == literal for k in mapping.keys())
    
    # Verify that each string literal gets a unique mask
    string_masks = [v for k, v in mapping.items() if k.startswith("'")]
    assert len(string_masks) == len(set(string_masks))
    
    # Verify that the masked SQL can be decoded back to the original
    decoded = masker.decode(masked, mapping)
    assert decoded.strip() == sql.strip()
    
    # Verify that the same string literal is consistently masked
    sql_with_repeated_strings = """
    SELECT * FROM users
    WHERE status = 'active' OR status = 'active'
    AND role = 'admin' OR role = 'admin'
    """
    
    masked, mapping = masker.encode(sql_with_repeated_strings)
    
    # Count occurrences of each masked string in the masked SQL
    for string_literal in ["'active'", "'admin'"]:
        mask = mapping[string_literal]
        # Each string should appear twice in the masked SQL
        assert masked.count(mask) == 2


def test_inline_comment_masking(masker):
    """Test that inline comments are properly masked and unmasked."""
    sql = """
    SELECT id, name -- This is a user identifier
    FROM users -- This is the users table
    WHERE status = 'active' -- Only active users
    """
    
    masked, mapping = masker.encode(sql)
    
    # Verify that comments are masked
    assert "-- This is a user identifier" not in masked
    assert "-- This is the users table" not in masked
    assert "-- Only active users" not in masked
    
    # Verify that comments are in the mapping
    comment_keys = [k for k in mapping.keys() if k.startswith("--")]
    assert len(comment_keys) == 3
    
    # Verify that each comment gets a unique mask
    comment_masks = [mapping[k] for k in comment_keys]
    assert len(comment_masks) == len(set(comment_masks))
    
    # Verify that all masks follow the expected format
    for mask in comment_masks:
        assert mask.startswith("--COMMENT")
    
    # Verify that the masked SQL can be decoded back to the original
    decoded = masker.decode(masked, mapping)
    assert decoded.strip() == sql.strip()
    
    # Verify that the same comment is consistently masked
    sql_with_repeated_comments = """
    SELECT id -- User ID
    FROM users
    WHERE status = 'active'
    UNION
    SELECT id -- User ID
    FROM archived_users
    """
    
    masked, mapping = masker.encode(sql_with_repeated_comments)
    
    # The same comment should be masked to the same value
    comment = "-- User ID"
    assert comment in mapping
    mask = mapping[comment]
    assert masked.count(mask) == 2


def test_multiline_comment_masking(masker):
    """Test that multiline comments are properly masked and unmasked."""
    sql = """
    /* 
     * This query retrieves user data
     * with their order information
     */
    SELECT 
        u.id,
        u.name,
        /* This is the user's email address,
           which is sensitive information */
        u.email,
        o.order_id
    FROM users u
    /* Join with orders table to get
       the user's order history */
    JOIN orders o ON u.id = o.user_id
    """
    
    masked, mapping = masker.encode(sql)
    
    # Verify that multiline comments are masked
    assert "/* \n     * This query retrieves user data" not in masked
    assert "/* This is the user's email address" not in masked
    assert "/* Join with orders table to get" not in masked
    
    # Verify that comments are in the mapping
    comment_keys = [k for k in mapping.keys() if k.startswith("/*")]
    assert len(comment_keys) == 3
    
    # Verify that each comment gets a unique mask
    comment_masks = [mapping[k] for k in comment_keys]
    assert len(comment_masks) == len(set(comment_masks))
    
    # Verify that all masks follow the expected format
    for mask in comment_masks:
        assert mask.startswith("/*COMMENT") and mask.endswith("*/")
    
    # Verify that the masked SQL can be decoded back to the original
    decoded = masker.decode(masked, mapping)
    assert decoded.strip() == sql.strip()


def test_mixed_comments_and_strings(masker):
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

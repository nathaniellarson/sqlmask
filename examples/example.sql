-- Example SQL query with various identifiers and features
WITH user_stats AS (
    SELECT 
        u.user_id,
        u.username,
        u.email,
        COUNT(o.order_id) AS total_orders,
        SUM(o.amount) AS total_spent,
        MAX(o.order_date) AS last_order_date
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    WHERE u.status = 'active'
    GROUP BY u.user_id, u.username, u.email
),
product_preferences AS (
    SELECT
        o.user_id,
        p.category_name,
        COUNT(*) AS purchase_count
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY o.user_id, p.category_name
    HAVING COUNT(*) > 1
)

SELECT
    us.user_id,
    us.username,
    us.email,
    us.total_orders,
    us.total_spent,
    us.last_order_date,
    STRING_AGG(pp.category_name, ', ') AS preferred_categories
FROM user_stats us
LEFT JOIN product_preferences pp ON us.user_id = pp.user_id
WHERE us.total_spent > 1000
ORDER BY us.total_spent DESC
LIMIT 100;

WITH user_orders AS (
    SELECT 
        u.id as user_id,
        u.name as user_name,
        COUNT(o.order_id) as order_count,
        SUM(o.total) as total_spent
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.id, u.name
),
order_items_summary AS (
    SELECT 
        o.user_id,
        p.category_id,
        COUNT(DISTINCT p.id) as unique_products,
        SUM(oi.quantity) as total_items
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    GROUP BY o.user_id, p.category_id
),
category_preferences AS (
    SELECT 
        ois.user_id,
        c.name as category_name,
        ois.unique_products,
        ois.total_items,
        RANK() OVER (PARTITION BY ois.user_id ORDER BY ois.total_items DESC) as category_rank
    FROM order_items_summary ois
    JOIN categories c ON ois.category_id = c.id
)
SELECT 
    uo.user_name,
    uo.order_count,
    uo.total_spent,
    STRING_AGG(
        CASE 
            WHEN cp.category_rank <= 3 
            THEN cp.category_name || ' (' || cp.total_items || ' items)'
        END,
        ', '
    ) as top_3_categories
FROM user_orders uo
LEFT JOIN category_preferences cp ON uo.user_id = cp.user_id
GROUP BY uo.user_id, uo.user_name, uo.order_count, uo.total_spent
HAVING uo.order_count > 0
ORDER BY uo.total_spent DESC
LIMIT 10;

-- m1 m2 m3 with m4 m5 and m6
WITH m7 AS (
    SELECT 
        m8.m9,
        m8.m10,
        m8.m11,
        COUNT(m12.m13) AS m14,
        SUM(m12.m15) AS m16,
        MAX(m12.m17) AS m18
    FROM m19 m8
    LEFT JOIN m20 m12 ON m8.m9 = m12.m9
    WHERE m8.m21 = 'active'
    GROUP BY m8.m9, m8.m10, m8.m11
),
m22 AS (
    SELECT
        m12.m9,
        m23.m24,
        COUNT(*) AS m25
    FROM m20 m12
    JOIN m26 m27 ON m12.m13 = m27.m13
    JOIN m28 m23 ON m27.m29 = m23.m29
    GROUP BY m12.m9, m23.m24
    HAVING COUNT(*) > 1
)

SELECT
    m30.m9,
    m30.m10,
    m30.m11,
    m30.m14,
    m30.m16,
    m30.m18,
    STRING_AGG(m31.m24, ', ') AS m32
FROM m7 m30
LEFT JOIN m22 m31 ON m30.m9 = m31.m9
WHERE m30.m16 > 1000
ORDER BY m30.m16 DESC
LIMIT 100;

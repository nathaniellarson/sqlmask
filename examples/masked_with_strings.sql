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
    WHERE m8.m21 = 'm22'
    GROUP BY m8.m9, m8.m10, m8.m11
),
m23 AS (
    SELECT
        m12.m9,
        m24.m25,
        COUNT(*) AS m26
    FROM m20 m12
    JOIN m27 m28 ON m12.m13 = m28.m13
    JOIN m29 m24 ON m28.m30 = m24.m30
    GROUP BY m12.m9, m24.m25
    HAVING COUNT(*) > 1
)

SELECT
    m31.m9,
    m31.m10,
    m31.m11,
    m31.m14,
    m31.m16,
    m31.m18,
    STRING_AGG(m32.m25, 'm33') AS m34
FROM m7 m31
LEFT JOIN m23 m32 ON m31.m9 = m32.m9
WHERE m31.m16 > 1000
ORDER BY m31.m16 DESC
LIMIT 100;

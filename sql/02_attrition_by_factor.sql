-- Attrition rate by factor level, with lift over the company average.
WITH long AS (
    SELECT 'Overtime' AS factor, CASE WHEN works_overtime THEN 'Yes' ELSE 'No' END AS level, left_company FROM stg_employees
    UNION ALL SELECT 'Job level', job_level::VARCHAR, left_company FROM stg_employees
    UNION ALL SELECT 'Job role', job_role, left_company FROM stg_employees
    UNION ALL SELECT 'Department', department, left_company FROM stg_employees
    UNION ALL SELECT 'Business travel', business_travel, left_company FROM stg_employees
    UNION ALL SELECT 'Marital status', marital_status, left_company FROM stg_employees
    UNION ALL SELECT 'Stock option level', stock_option_level::VARCHAR, left_company FROM stg_employees
    UNION ALL SELECT 'Tenure', tenure_band, left_company FROM stg_employees
    UNION ALL SELECT 'Income quartile', 'Q' || income_quartile::VARCHAR, left_company FROM stg_employees
    UNION ALL SELECT 'Work-life balance (1 low to 4 high)', work_life_balance::VARCHAR, left_company FROM stg_employees
    UNION ALL SELECT 'Job satisfaction (1 low to 4 high)', job_satisfaction::VARCHAR, left_company FROM stg_employees
),
overall AS (SELECT AVG(left_company::INT) AS rate FROM stg_employees)
SELECT
    factor,
    level,
    COUNT(*) AS employees,
    SUM(left_company::INT) AS leavers,
    ROUND(100 * AVG(left_company::INT), 1) AS attrition_pct,
    ROUND(AVG(left_company::INT) / overall.rate, 2) AS lift_vs_company
FROM long, overall
GROUP BY factor, level, overall.rate
ORDER BY factor, level;

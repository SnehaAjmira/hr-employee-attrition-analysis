-- Estimated replacement cost of attrition by department.
-- ASSUMPTION: replacement cost = 50% of annual salary. Change the value below to test other rates.
WITH params AS (SELECT 0.50 AS replacement_cost_rate)
SELECT
    department,
    COUNT(*) FILTER (WHERE left_company) AS leavers,
    ROUND(SUM(monthly_income * 12) FILTER (WHERE left_company)) AS leaver_annual_salary,
    ROUND(SUM(monthly_income * 12 * replacement_cost_rate) FILTER (WHERE left_company)) AS est_replacement_cost,
    ROUND(SUM(monthly_income * 12 * replacement_cost_rate) FILTER (WHERE left_company AND works_overtime)) AS est_cost_overtime_leavers
FROM stg_employees, params
GROUP BY department
ORDER BY est_replacement_cost DESC;

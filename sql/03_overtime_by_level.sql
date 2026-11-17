-- Interaction of overtime and job level: where risk compounds.
SELECT
    job_level,
    CASE WHEN works_overtime THEN 'Overtime' ELSE 'No overtime' END AS overtime,
    COUNT(*) AS employees,
    SUM(left_company::INT) AS leavers,
    ROUND(100 * AVG(left_company::INT), 1) AS attrition_pct
FROM stg_employees
GROUP BY ALL
ORDER BY job_level, overtime;

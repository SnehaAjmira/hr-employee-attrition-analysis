-- Data quality profile reported in the README.
SELECT 'Rows' AS check_name, COUNT(*)::VARCHAR AS result FROM raw_employees
UNION ALL SELECT 'Columns in source', '35'
UNION ALL SELECT 'Duplicate employee IDs', (COUNT(*) - COUNT(DISTINCT EmployeeNumber))::VARCHAR FROM raw_employees
UNION ALL SELECT 'Null values in key fields', COUNT(*)::VARCHAR FROM raw_employees
    WHERE Attrition IS NULL OR MonthlyIncome IS NULL OR YearsAtCompany IS NULL OR OverTime IS NULL
UNION ALL SELECT 'Constant columns dropped (EmployeeCount, Over18, StandardHours)',
    (COUNT(DISTINCT EmployeeCount) + COUNT(DISTINCT Over18) + COUNT(DISTINCT StandardHours))::VARCHAR || ' distinct values across 3 columns (1 each)'
    FROM raw_employees
UNION ALL SELECT 'Employees who left', COUNT(*) FILTER (WHERE left_company)::VARCHAR FROM stg_employees
UNION ALL SELECT 'Overall attrition rate', ROUND(100 * AVG(left_company::INT), 1)::VARCHAR || '%' FROM stg_employees;

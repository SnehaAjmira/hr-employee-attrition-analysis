-- Median profile of leavers vs stayers.
SELECT
    CASE WHEN left_company THEN 'Left' ELSE 'Stayed' END AS status,
    COUNT(*) AS employees,
    MEDIAN(age) AS median_age,
    MEDIAN(monthly_income) AS median_monthly_income,
    MEDIAN(years_at_company) AS median_years_at_company,
    MEDIAN(total_working_years) AS median_total_working_years,
    MEDIAN(distance_from_home) AS median_distance_from_home,
    ROUND(100 * AVG(works_overtime::INT), 1) AS overtime_pct,
    ROUND(100 * AVG((stock_option_level = 0)::INT), 1) AS no_stock_options_pct
FROM stg_employees
GROUP BY ALL
ORDER BY status;

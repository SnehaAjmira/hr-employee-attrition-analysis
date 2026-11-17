-- Staging: load HR records, drop constant columns, derive analysis bands and labels.
CREATE OR REPLACE TABLE raw_employees AS
SELECT * FROM read_csv_auto('data/raw/emp_attrition.csv', all_varchar = true);

CREATE OR REPLACE TABLE stg_employees AS
SELECT
    CAST(EmployeeNumber AS INTEGER)       AS employee_id,
    CAST(Age AS INTEGER)                  AS age,
    Attrition = 'Yes'                     AS left_company,
    Department                            AS department,
    JobRole                               AS job_role,
    CAST(JobLevel AS INTEGER)             AS job_level,
    OverTime = 'Yes'                      AS works_overtime,
    REPLACE(BusinessTravel, '_', ' ')     AS business_travel,
    MaritalStatus                         AS marital_status,
    CAST(MonthlyIncome AS INTEGER)        AS monthly_income,
    CAST(StockOptionLevel AS INTEGER)     AS stock_option_level,
    CAST(YearsAtCompany AS INTEGER)       AS years_at_company,
    CAST(YearsSinceLastPromotion AS INTEGER) AS years_since_promotion,
    CAST(DistanceFromHome AS INTEGER)     AS distance_from_home,
    CAST(TotalWorkingYears AS INTEGER)    AS total_working_years,
    CAST(NumCompaniesWorked AS INTEGER)   AS companies_worked,
    CAST(JobSatisfaction AS INTEGER)      AS job_satisfaction,
    CAST(EnvironmentSatisfaction AS INTEGER) AS environment_satisfaction,
    CAST(WorkLifeBalance AS INTEGER)      AS work_life_balance,
    CASE
        WHEN CAST(YearsAtCompany AS INTEGER) <= 1  THEN '1) 0-1 years'
        WHEN CAST(YearsAtCompany AS INTEGER) <= 3  THEN '2) 2-3 years'
        WHEN CAST(YearsAtCompany AS INTEGER) <= 5  THEN '3) 4-5 years'
        WHEN CAST(YearsAtCompany AS INTEGER) <= 10 THEN '4) 6-10 years'
        ELSE '5) 11+ years'
    END AS tenure_band,
    NTILE(4) OVER (ORDER BY CAST(MonthlyIncome AS INTEGER)) AS income_quartile
FROM raw_employees;

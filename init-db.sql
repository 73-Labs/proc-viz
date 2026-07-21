-- Database: DummyDB
-- Exported: 2026-07-21 20:15:41

-- ============================================
-- Schema: db_accessadmin
-- ============================================


-- ============================================
-- Schema: db_backupoperator
-- ============================================


-- ============================================
-- Schema: db_datareader
-- ============================================


-- ============================================
-- Schema: db_datawriter
-- ============================================


-- ============================================
-- Schema: db_ddladmin
-- ============================================


-- ============================================
-- Schema: db_denydatareader
-- ============================================


-- ============================================
-- Schema: db_denydatawriter
-- ============================================


-- ============================================
-- Schema: db_owner
-- ============================================


-- ============================================
-- Schema: db_securityadmin
-- ============================================


-- ============================================
-- Schema: dbo
-- ============================================

-- Tables in dbo
CREATE TABLE [dbo].[Employees] (
    [EmployeeID] int IDENTITY(1,1) PRIMARY KEY NOT NULL,
    [Name] nvarchar(100) NOT NULL,
    [Department] nvarchar(50),
    [Salary] decimal(10,2),
    [ManagerID] int,
    [CreatedDate] datetime DEFAULT (getdate())
);

-- Procedures in dbo
CREATE PROCEDURE sp_GetDepartmentStats
    @Department NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @EmployeeCount INT;
    DECLARE @AvgSalary DECIMAL(10, 2);
    DECLARE @MaxSalary DECIMAL(10, 2);
    DECLARE @MinSalary DECIMAL(10, 2);
    DECLARE @TotalPayroll DECIMAL(15, 2);
    
    -- Get department statistics
    SELECT 
        @EmployeeCount = COUNT(*),
        @AvgSalary = AVG(Salary),
        @MaxSalary = MAX(Salary),
        @MinSalary = MIN(Salary),
        @TotalPayroll = SUM(Salary)
    FROM Employees
    WHERE Department = @Department;
    
    -- Display the statistics
    PRINT '';
    PRINT '===== Department Statistics =====';
    PRINT 'Department: ' + @Department;
    PRINT 'Total Employees: ' + CAST(@EmployeeCount AS NVARCHAR(10));
    PRINT 'Average Salary: $' + CAST(CAST(@AvgSalary AS DECIMAL(10, 2)) AS NVARCHAR(20));
    PRINT 'Max Salary: $' + CAST(@MaxSalary AS NVARCHAR(20));
    PRINT 'Min Salary: $' + CAST(@MinSalary AS NVARCHAR(20));
    PRINT 'Total Payroll: $' + CAST(@TotalPayroll AS NVARCHAR(20));
    PRINT '=================================';
    PRINT '';
END;

CREATE PROCEDURE sp_GetEmployeeInfo
    @EmployeeID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ManagerID INT;
    DECLARE @EmployeeName NVARCHAR(100);
    
    -- Get the employee details
    SELECT 
        @EmployeeID = EmployeeID,
        @EmployeeName = Name,
        @ManagerID = ManagerID
    FROM Employees
    WHERE EmployeeID = @EmployeeID;
    
    -- Print employee info
    PRINT '========== Employee Info ==========';
    PRINT 'Employee ID: ' + CAST(@EmployeeID AS NVARCHAR(10));
    PRINT 'Employee Name: ' + @EmployeeName;
    
    -- If employee has a manager, call the other procedure
    IF @ManagerID IS NOT NULL
    BEGIN
        PRINT 'Manager ID: ' + CAST(@ManagerID AS NVARCHAR(10));
        PRINT '--- Fetching Manager Details ---';
        EXEC sp_GetManagerInfo @ManagerID;
    END
    ELSE
    BEGIN
        PRINT 'Manager: None (Top Level)';
    END
    
    PRINT '===================================';
END;


CREATE PROCEDURE sp_GetManagerInfo
    @ManagerID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ManagerName NVARCHAR(100);
    DECLARE @ManagerSalary DECIMAL(10, 2);
    DECLARE @ManagerDepartment NVARCHAR(50);
    DECLARE @DirectReports INT;
    
    -- Get manager details
    SELECT 
        @ManagerName = Name,
        @ManagerSalary = Salary,
        @ManagerDepartment = Department
    FROM Employees
    WHERE EmployeeID = @ManagerID;
    
    -- Count direct reports
    SELECT @DirectReports = COUNT(*)
    FROM Employees
    WHERE ManagerID = @ManagerID;
    
    -- Print manager info
    PRINT '========== Manager Info ==========';
    PRINT 'Manager ID: ' + CAST(@ManagerID AS NVARCHAR(10));
    PRINT 'Manager Name: ' + @ManagerName;
    PRINT 'Department: ' + @ManagerDepartment;
    PRINT 'Salary: $' + CAST(@ManagerSalary AS NVARCHAR(20));
    PRINT 'Direct Reports: ' + CAST(@DirectReports AS NVARCHAR(10));
    
    -- Call the new procedure to show department statistics
    PRINT '';
    PRINT 'Calling sp_GetDepartmentStats...';
    EXEC sp_GetDepartmentStats @ManagerDepartment;
    
    -- If manager has direct reports, show first one
    IF @DirectReports > 0
    BEGIN
        DECLARE @FirstReportID INT;
        SELECT TOP 1 @FirstReportID = EmployeeID
        FROM Employees
        WHERE ManagerID = @ManagerID;
        
        PRINT '--- Fetching First Direct Report ---';
        EXEC sp_GetEmployeeInfo @FirstReportID;
    END
    
    PRINT '===================================';
END;


-- ============================================
-- Schema: FunctionSchema
-- ============================================

-- Functions in FunctionSchema
CREATE FUNCTION FunctionSchema.fn_GetDepartmentAverage(@Department NVARCHAR(50))
RETURNS DECIMAL(10, 2)
AS
BEGIN
    DECLARE @AvgSalary DECIMAL(10, 2);
    
    SELECT @AvgSalary = AVG(Salary)
    FROM Employees
    WHERE Department = @Department;
    
    RETURN ISNULL(@AvgSalary, 0);
END;

CREATE FUNCTION FunctionSchema.fn_GetDepartmentDetails(@Department NVARCHAR(50))
RETURNS TABLE
AS
RETURN
(
    SELECT 
        E.EmployeeID,
        E.Name,
        E.Department,
        E.Salary,
        SalaryWithCompensation = FunctionSchema.fn_GetEmployeeSalary(E.EmployeeID),
        ManagerBonus = CASE 
            WHEN EXISTS (SELECT 1 FROM Employees WHERE ManagerID = E.EmployeeID)
            THEN FunctionSchema.fn_GetManagerBonus(E.EmployeeID)
            ELSE 0
        END,
        DirectReportCount = (SELECT COUNT(*) FROM Employees WHERE ManagerID = E.EmployeeID),
        DepartmentAvgSalary = FunctionSchema.fn_GetDepartmentAverage(E.Department)
    FROM Employees E
    WHERE E.Department = @Department
);

-- =====================================================
CREATE FUNCTION FunctionSchema.fn_GetEmployeeSalary(@EmployeeID INT)
RETURNS DECIMAL(10, 2)
AS
BEGIN
    DECLARE @Salary DECIMAL(10, 2);
    DECLARE @ManagerID INT;
    DECLARE @ManagerBonus DECIMAL(10, 2);
    
    -- Get employee salary
    SELECT 
        @Salary = Salary,
        @ManagerID = ManagerID
    FROM Employees
    WHERE EmployeeID = @EmployeeID;
    
    -- If employee is a manager (has reports), calculate manager bonus
    IF EXISTS (SELECT 1 FROM Employees WHERE ManagerID = @EmployeeID)
    BEGIN
        SET @ManagerBonus = FunctionSchema.fn_GetManagerBonus(@EmployeeID);
        SET @Salary = @Salary + @ManagerBonus;
    END
    
    RETURN ISNULL(@Salary, 0);
END;

CREATE FUNCTION FunctionSchema.fn_GetManagerBonus(@ManagerID INT)
RETURNS DECIMAL(10, 2)
AS
BEGIN
    DECLARE @Bonus DECIMAL(10, 2) = 0;
    DECLARE @ManagerSalary DECIMAL(10, 2);
    DECLARE @Department NVARCHAR(50);
    DECLARE @DepartmentAvg DECIMAL(10, 2);
    DECLARE @DirectReports INT;
    
    -- Get manager's salary and department
    SELECT 
        @ManagerSalary = Salary,
        @Department = Department
    FROM Employees
    WHERE EmployeeID = @ManagerID;
    
    -- Count direct reports
    SELECT @DirectReports = COUNT(*)
    FROM Employees
    WHERE ManagerID = @ManagerID;
    
    -- Get department average using the department stats function
    SET @DepartmentAvg = FunctionSchema.fn_GetDepartmentAverage(@Department);
    
    -- Bonus: 5% per direct report + 2% if above department average
    SET @Bonus = (@ManagerSalary * @DirectReports * 0.05);
    
    IF @ManagerSalary > @DepartmentAvg
    BEGIN
        SET @Bonus = @Bonus + (@ManagerSalary * 0.02);
    END
    
    RETURN ISNULL(@Bonus, 0);
END;


-- ============================================
-- Schema: guest
-- ============================================


-- ============================================
-- Schema: INFORMATION_SCHEMA
-- ============================================


-- ============================================
-- Schema: sys
-- ============================================


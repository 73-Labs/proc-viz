-- Create SQL Server login for app
IF NOT EXISTS (SELECT * FROM sys.sql_logins WHERE name = 'appuser')
BEGIN
    CREATE LOGIN [appuser] WITH PASSWORD = 'AppPassword123!';
END

-- Create database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'procviz')
BEGIN
    CREATE DATABASE [procviz];
END

-- Switch to new database
USE [procviz];

-- Create database user from login
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'appuser')
BEGIN
    CREATE USER [appuser] FOR LOGIN [appuser];
END

-- Grant permissions
ALTER ROLE [db_owner] ADD MEMBER [appuser];

-- Create sample table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'processes')
BEGIN
    CREATE TABLE [dbo].[processes] (
        [id] INT PRIMARY KEY IDENTITY(1,1),
        [name] NVARCHAR(255) NOT NULL,
        [status] NVARCHAR(50) NOT NULL,
        [created_at] DATETIME DEFAULT GETUTCDATE()
    );
END

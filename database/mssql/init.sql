-- ShopStream Database Schema - MS SQL Server
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'ShopStreamDB')
BEGIN
    CREATE DATABASE ShopStreamDB;
END
GO

USE ShopStreamDB;
GO
 
 
-- USERS TABLE
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) UNIQUE NOT NULL,
    email NVARCHAR(100) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
GO

-- ORDERS TABLE
CREATE TABLE orders (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    status NVARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(10,2) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
GO

-- PAYMENTS TABLE
CREATE TABLE payments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    payment_method NVARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status NVARCHAR(20) DEFAULT 'pending',
    transaction_id NVARCHAR(100) UNIQUE,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
GO

-- TRANSACTIONS TABLE
CREATE TABLE transactions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    transaction_type NVARCHAR(50) NOT NULL,
    status NVARCHAR(20) DEFAULT 'completed',
    description NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
GO
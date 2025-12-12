"""
MySQL Database Connection Script for Flask
Similar to connect.php but written in Python for Flask applications.

This module provides a simple interface to connect to MySQL database.
It reads configuration from environment variables and provides connection pooling.
"""

import os
import mysql.connector
from mysql.connector import pooling, Error, errorcode
from typing import Optional


# Database configuration from environment variables
# Default values are set for local MySQL database
# Override with environment variables for different environments
# To use remote MySQL, set: DB_HOST=ilmuwanutara.my DB_USER=ilmuwanutara_e2eewater DB_PASSWORD=e2eeWater@2025
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')  # MySQL host: '127.0.0.1' for local, 'ilmuwanutara.my' for remote
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_USER = os.getenv('DB_USER', 'root')  # Local MySQL user
DB_PASSWORD = os.getenv('DB_PASSWORD', '')  # Local MySQL password (empty by default)
DB_NAME = os.getenv('DB_NAME', 'ilmuwanutara_e2eewater')

# Connection pool configuration
POOL_NAME = 'flask_pool'
POOL_SIZE = 5
POOL_RESET_SESSION = True

# Global connection pool
_pool: Optional[mysql.connector.pooling.MySQLConnectionPool] = None


def get_connection_pool() -> mysql.connector.pooling.MySQLConnectionPool:
    """
    Get or create the MySQL connection pool.
    
    Returns:
        MySQLConnectionPool: The connection pool instance
        
    Raises:
        Error: If connection pool creation fails
    """
    global _pool
    
    if _pool is None:
        try:
            _pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=POOL_NAME,
                pool_size=POOL_SIZE,
                pool_reset_session=POOL_RESET_SESSION,
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False,
                raise_on_warnings=False
            )
            print(f"MySQL connection pool created successfully: {POOL_NAME}")
        except Error as err:
            print(f"Error creating connection pool: {err}")
            raise
    
    return _pool


def get_connection():
    """
    Get a connection from the pool.
    
    Returns:
        MySQLConnection: A database connection from the pool
        
    Raises:
        Error: If connection retrieval fails
    """
    pool = get_connection_pool()
    try:
        connection = pool.get_connection()
        return connection
    except Error as err:
        print(f"Error getting connection from pool: {err}")
        raise


def close_connection(connection):
    """
    Return a connection to the pool.
    
    Args:
        connection: The MySQL connection to return to the pool
    """
    if connection and connection.is_connected():
        connection.close()


def test_connection() -> bool:
    """
    Test the database connection.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        close_connection(conn)
        
        if result:
            print("Database connection test successful!")
            return True
        else:
            print("Database connection test failed: No result returned")
            return False
    except Error as err:
        print(f"Database connection test failed: {err}")
        return False


def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = True):
    """
    Execute a SQL query and return results.
    
    Args:
        query: SQL query string
        params: Optional tuple of parameters for parameterized queries
        fetch: Whether to fetch and return results (default: True)
        
    Returns:
        List of tuples if fetch=True, None otherwise
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            results = cursor.fetchall()
            conn.commit()
            return results
        else:
            conn.commit()
            return None
            
    except Error as err:
        if conn:
            conn.rollback()
        print(f"Error executing query: {err}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            close_connection(conn)


def execute_query_dict(query: str, params: Optional[tuple] = None, fetch: bool = True):
    """
    Execute a SQL query and return results as dictionaries.
    
    Args:
        query: SQL query string
        params: Optional tuple of parameters for parameterized queries
        fetch: Whether to fetch and return results (default: True)
        
    Returns:
        List of dictionaries if fetch=True, None otherwise
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            results = cursor.fetchall()
            conn.commit()
            return results
        else:
            conn.commit()
            return None
            
    except Error as err:
        if conn:
            conn.rollback()
        print(f"Error executing query: {err}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            close_connection(conn)


# Example usage
if __name__ == "__main__":
    print("Testing MySQL connection...")
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"User: {DB_USER}")
    print(f"Database: {DB_NAME}")
    print(f"Password: {'*' * len(DB_PASSWORD) if DB_PASSWORD else '(not set)'}")
    print("-" * 50)
    
    # Test connection
    if test_connection():
        print("\nConnection pool is working correctly!")
        
        # Example: Execute a simple query
        try:
            results = execute_query("SHOW TABLES")
            print(f"\nFound {len(results)} tables in database:")
            for table in results:
                print(f"  - {table[0]}")
        except Error as err:
            print(f"Error querying tables: {err}")
    else:
        print("\nFailed to connect to database. Please check your configuration.")


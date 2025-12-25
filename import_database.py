#!/usr/bin/env python3
"""
Database Import Script
Alternative to phpMyAdmin for importing SQL files into MySQL database.

Usage:
    python import_database.py <sql_file_path>
    
Example:
    python import_database.py backup.sql
"""

import sys
import os
import mysql.connector
from mysql.connector import Error
import argparse
from pathlib import Path

# Import database configuration from connect.py
try:
    from connect import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
except ImportError:
    # Fallback to environment variables or defaults
    import os
    DB_HOST = os.getenv('DB_HOST', 'ilmuwanutara.my')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'ilmuwanutara_e2eewater')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'e2eeWater@2025')
    DB_NAME = os.getenv('DB_NAME', 'ilmuwanutara_e2eewater')


def read_sql_file(file_path):
    """Read SQL file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        print("Warning: UTF-8 encoding failed, trying latin-1...")
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def split_sql_statements(sql_content):
    """
    Split SQL content into individual statements.
    Handles multi-line statements and comments.
    """
    statements = []
    current_statement = []
    in_string = False
    string_char = None
    i = 0
    
    while i < len(sql_content):
        char = sql_content[i]
        
        # Handle string literals
        if char in ("'", '"', '`') and (i == 0 or sql_content[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            current_statement.append(char)
        
        # Handle comments
        elif not in_string:
            # Single-line comment
            if char == '-' and i + 1 < len(sql_content) and sql_content[i+1] == '-':
                # Skip until end of line
                while i < len(sql_content) and sql_content[i] != '\n':
                    i += 1
                continue
            # Multi-line comment
            elif char == '/' and i + 1 < len(sql_content) and sql_content[i+1] == '*':
                # Skip until */
                i += 2
                while i + 1 < len(sql_content):
                    if sql_content[i] == '*' and sql_content[i+1] == '/':
                        i += 2
                        break
                    i += 1
                continue
            # Statement delimiter
            elif char == ';' and not in_string:
                statement = ''.join(current_statement).strip()
                if statement:
                    statements.append(statement)
                current_statement = []
            else:
                current_statement.append(char)
        else:
            current_statement.append(char)
        
        i += 1
    
    # Add remaining statement if any
    if current_statement:
        statement = ''.join(current_statement).strip()
        if statement:
            statements.append(statement)
    
    return statements


def import_database(sql_file_path, create_db=False, drop_existing=False):
    """
    Import SQL file into MySQL database.
    
    Args:
        sql_file_path: Path to SQL file
        create_db: Create database if it doesn't exist
        drop_existing: Drop existing database before import (WARNING: Deletes all data!)
    """
    # Check if file exists
    if not os.path.exists(sql_file_path):
        print(f"Error: SQL file not found: {sql_file_path}")
        return False
    
    # Get file size
    file_size = os.path.getsize(sql_file_path)
    print(f"SQL file: {sql_file_path}")
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    print(f"Connecting to database: {DB_HOST}:{DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print("-" * 60)
    
    connection = None
    try:
        # Connect to MySQL server (without selecting database first)
        print("Connecting to MySQL server...")
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        if connection.is_connected():
            print("✓ Connected to MySQL server")
            cursor = connection.cursor()
            
            # Check if database exists
            cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            db_exists = cursor.fetchone() is not None
            
            if db_exists:
                print(f"✓ Database '{DB_NAME}' exists")
                if drop_existing:
                    print(f"⚠ WARNING: Dropping existing database '{DB_NAME}'...")
                    cursor.execute(f"DROP DATABASE `{DB_NAME}`")
                    print(f"✓ Database dropped")
                    db_exists = False
            
            # Create database if needed
            if not db_exists:
                if create_db or drop_existing:
                    print(f"Creating database '{DB_NAME}'...")
                    cursor.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    print(f"✓ Database created")
                else:
                    print(f"Error: Database '{DB_NAME}' does not exist. Use --create-db to create it.")
                    return False
            
            # Select database
            cursor.execute(f"USE `{DB_NAME}`")
            print(f"✓ Using database '{DB_NAME}'")
            
            # Read SQL file
            print("\nReading SQL file...")
            sql_content = read_sql_file(sql_file_path)
            print(f"✓ File read successfully ({len(sql_content)} characters)")
            
            # Split into statements
            print("Parsing SQL statements...")
            statements = split_sql_statements(sql_content)
            print(f"✓ Found {len(statements)} SQL statements")
            
            # Execute statements
            print("\nExecuting SQL statements...")
            executed = 0
            failed = 0
            
            for i, statement in enumerate(statements, 1):
                try:
                    # Skip empty statements
                    if not statement.strip():
                        continue
                    
                    # Execute statement
                    cursor.execute(statement)
                    
                    # Commit after each statement
                    connection.commit()
                    
                    executed += 1
                    
                    # Progress indicator
                    if i % 100 == 0:
                        print(f"  Progress: {i}/{len(statements)} statements executed...")
                
                except Error as e:
                    failed += 1
                    print(f"\n⚠ Error in statement {i}: {str(e)[:100]}")
                    # Print first 200 chars of failed statement for debugging
                    print(f"  Statement preview: {statement[:200]}...")
                    
                    # Ask if should continue
                    if failed == 1:
                        response = input("\nContinue despite errors? (y/n): ").lower()
                        if response != 'y':
                            print("Import cancelled by user.")
                            return False
            
            print("\n" + "=" * 60)
            print("Import Summary:")
            print(f"  ✓ Successfully executed: {executed} statements")
            if failed > 0:
                print(f"  ⚠ Failed: {failed} statements")
            print("=" * 60)
            
            # Verify import
            print("\nVerifying import...")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"✓ Found {len(tables)} tables in database:")
            for table in tables[:10]:  # Show first 10 tables
                print(f"  - {table[0]}")
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more tables")
            
            print("\n✓ Database import completed successfully!")
            return True
            
    except Error as e:
        print(f"\n✗ MySQL Error: {e}")
        return False
    
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n✓ MySQL connection closed")


def main():
    parser = argparse.ArgumentParser(
        description='Import SQL file into MySQL database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python import_database.py backup.sql
  python import_database.py backup.sql --create-db
  python import_database.py backup.sql --drop-existing
  
Note: --drop-existing will DELETE all existing data in the database!
        """
    )
    
    parser.add_argument(
        'sql_file',
        type=str,
        help='Path to SQL file to import'
    )
    
    parser.add_argument(
        '--create-db',
        action='store_true',
        help='Create database if it does not exist'
    )
    
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop existing database before import (WARNING: Deletes all data!)'
    )
    
    args = parser.parse_args()
    
    # Confirm drop operation
    if args.drop_existing:
        print("⚠ WARNING: This will DELETE all existing data in the database!")
        response = input(f"Are you sure you want to drop database '{DB_NAME}'? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    # Import database
    success = import_database(
        args.sql_file,
        create_db=args.create_db,
        drop_existing=args.drop_existing
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()






























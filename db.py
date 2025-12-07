import os
from datetime import datetime
import re
import json
from db_encryption import get_db_encryption

# Detect database type from environment
DB_TYPE = os.getenv('DB_TYPE', 'mysql').lower()

# Support both MySQL and PostgreSQL
if DB_TYPE == 'postgresql':
    try:
        import psycopg2
        from psycopg2 import pool, Error, errorcode
        from psycopg2.extras import RealDictCursor
        POSTGRESQL_AVAILABLE = True
    except ImportError:
        print("WARNING: psycopg2 not installed. Install with: pip install psycopg2-binary")
        POSTGRESQL_AVAILABLE = False
        DB_TYPE = 'mysql'  # Fallback to MySQL
else:
    POSTGRESQL_AVAILABLE = False

if DB_TYPE == 'mysql':
    import mysql.connector
    from mysql.connector import pooling, Error, errorcode

# Parse DATABASE_URL if provided (PostgreSQL style)
DATABASE_URL = os.getenv('DATABASE_URL', '')
if DATABASE_URL and DB_TYPE == 'postgresql':
    # Parse postgresql://user:password@host:port/dbname
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    DB_USER = urllib.parse.unquote(parsed.username or 'postgres')
    DB_PASSWORD = urllib.parse.unquote(parsed.password or '')
    DB_HOST = parsed.hostname or 'localhost'
    DB_PORT = parsed.port or 5432
    DB_NAME = parsed.path.lstrip('/') or 'ilmuwanutara_e2eewater'
else:
    # Environment-driven database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432' if DB_TYPE == 'postgresql' else '3306'))
    DB_USER = os.getenv('DB_USER', 'postgres' if DB_TYPE == 'postgresql' else 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'ilmuwanutara_e2eewater')

_pool = None


def _get_connection(pool):
    """Get a connection from the pool (works for both MySQL and PostgreSQL)."""
    if DB_TYPE == 'postgresql':
        return pool.getconn()
    else:
        return pool.get_connection()


def _return_connection(pool, conn):
    """Return a connection to the pool (works for both MySQL and PostgreSQL)."""
    if DB_TYPE == 'postgresql':
        pool.putconn(conn)
    else:
        conn.close()


def _get_cursor(conn, dictionary=False):
    """Get a cursor (works for both MySQL and PostgreSQL)."""
    if DB_TYPE == 'postgresql':
        if dictionary:
            return conn.cursor(cursor_factory=RealDictCursor)
        else:
            return conn.cursor()
    else:
        return conn.cursor(dictionary=dictionary)


def _create_database_if_missing() -> None:
    """
    Create database if missing. Uses environment variable for DB_NAME.
    Note: DB_NAME comes from environment, not user input, so f-string is safe here.
    For additional security, we validate DB_NAME contains only safe characters.
    """
    try:
        # Validate DB_NAME contains only safe characters (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', DB_NAME):
            raise ValueError(f"Invalid database name: {DB_NAME} contains unsafe characters")
        
        tmp_conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        tmp_cur = tmp_conn.cursor()
        # Use parameterized query where possible, but CREATE DATABASE doesn't support parameters
        # Since DB_NAME comes from environment variable (not user input), this is safe
        tmp_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
        tmp_conn.commit()
        tmp_cur.close()
        tmp_conn.close()
    except Exception as e:
        print(f"MySQL create database error: {e}")


def _ensure_schema(conn) -> None:
    # Create cursor based on database type
    if DB_TYPE == 'postgresql':
        cur = conn.cursor()
        quote_char = '"'
        auto_inc = 'SERIAL'
        datetime_type = 'TIMESTAMP'
        double_type = 'DOUBLE PRECISION'
    else:
        cur = conn.cursor(buffered=True)  # MySQL buffered cursor
        quote_char = '`'
        auto_inc = 'INT AUTO_INCREMENT'
        datetime_type = 'DATETIME'
        double_type = 'DOUBLE'
    
    # Sensor type master table (defaults and metadata)
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {quote_char}sensor_type{quote_char} (
            id {auto_inc} PRIMARY KEY,
            type_name VARCHAR(100) NOT NULL UNIQUE,
            unit VARCHAR(50) DEFAULT NULL,
            default_min {double_type} NULL,
            default_max {double_type} NULL,
            description TEXT NULL
        )
        """
    )
    # Seed default sensor types if table is empty
    try:
        cur.execute(f"SELECT COUNT(*) FROM {quote_char}sensor_type{quote_char}")
        row = cur.fetchone()
        count = int(row[0]) if row and row[0] is not None else 0
        if count == 0:
            print("Seeding default sensor types...")
            cur.executemany(
                f"""
                INSERT INTO {quote_char}sensor_type{quote_char} (type_name, unit, default_min, default_max, description)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [
                    ("ph", None, 6.5, 8.5, "pH level"),
                    ("tds", "ppm", 0.0, 500.0, "Total Dissolved Solids"),
                    ("turbidity", "NTU", 0.0, 5.0, "Turbidity"),
                ],
            )
            # Consume any results after executemany
            try:
                cur.fetchall()
            except:
                pass
            print("Successfully seeded default sensor types")
        else:
            print(f"sensor_type table already has {count} entries")
        # Ensure all results are consumed
        cur.fetchall()  # Consume any remaining results
    except Exception as e:
        print(f"ERROR: Failed to seed sensor types: {e}")
        import traceback
        traceback.print_exc()
        # Try to consume any unread results
        try:
            cur.fetchall()
        except:
            pass
    # water_readings table removed - using sensor_data table only
    # cur.execute(
    #     """
    #     CREATE TABLE IF NOT EXISTS water_readings (
    #         id INT AUTO_INCREMENT PRIMARY KEY,
    #         tds TEXT,
    #         ph TEXT,
    #         turbidity TEXT,
    #         safe_to_drink TINYINT(1),
    #         safety_issues TEXT,
    #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     )
    #     """
    # )
    # User credentials table for authentication (sr_no, email, name, username, password)
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {quote_char}user_cred{quote_char} (
            sr_no {auto_inc} PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            username VARCHAR(150) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Sensors table for device registration and key management
    if DB_TYPE == 'postgresql':
        # PostgreSQL: Use VARCHAR with CHECK instead of ENUM
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quote_char}sensors{quote_char} (
                id {auto_inc} PRIMARY KEY,
                device_id VARCHAR(100) NOT NULL,
                device_type VARCHAR(100) NOT NULL,
                sensor_type_id INT NULL,
                location VARCHAR(255) DEFAULT NULL,
                public_key TEXT NULL,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'revoked')),
                registered_at {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                last_seen {datetime_type} DEFAULT NULL,
                min_threshold {double_type} NULL,
                max_threshold {double_type} NULL,
                user_id INT NULL,
                CONSTRAINT fk_sensors_user FOREIGN KEY (user_id)
                    REFERENCES {quote_char}user_cred{quote_char}(sr_no) ON UPDATE CASCADE ON DELETE CASCADE
            )
            """
        )
        # Create indexes separately for PostgreSQL
        try:
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_sensors_user_id ON {quote_char}sensors{quote_char}(user_id)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_sensors_device_id ON {quote_char}sensors{quote_char}(device_id)")
            cur.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS unique_user_device ON {quote_char}sensors{quote_char}(user_id, device_id)")
        except Exception:
            pass
    else:
        # MySQL: Use ENUM
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quote_char}sensors{quote_char} (
                id {auto_inc} PRIMARY KEY,
                device_id VARCHAR(100) NOT NULL,
                device_type VARCHAR(100) NOT NULL,
                sensor_type_id INT NULL,
                location VARCHAR(255) DEFAULT NULL,
                public_key TEXT NULL,
                status ENUM('active', 'inactive', 'revoked') DEFAULT 'active',
                registered_at {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                last_seen {datetime_type} DEFAULT NULL,
                min_threshold {double_type} NULL,
                max_threshold {double_type} NULL,
                user_id INT NULL,
                INDEX idx_sensors_user_id (user_id),
                INDEX idx_sensors_device_id (device_id),
                UNIQUE KEY unique_user_device (user_id, device_id),
                CONSTRAINT fk_sensors_user FOREIGN KEY (user_id)
                    REFERENCES {quote_char}user_cred{quote_char}(sr_no) ON UPDATE CASCADE ON DELETE CASCADE
            )
            """
        )
    # Add user_id column if it doesn't exist (for existing databases) - MySQL only
    if DB_TYPE != 'postgresql':
        try:
            cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} ADD COLUMN user_id INT NULL")
            cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} ADD INDEX idx_sensors_user_id (user_id)")
            cur.execute(f"""
                ALTER TABLE {quote_char}sensors{quote_char} 
                ADD CONSTRAINT fk_sensors_user 
                FOREIGN KEY (user_id) REFERENCES {quote_char}user_cred{quote_char}(sr_no) ON UPDATE CASCADE ON DELETE CASCADE
            """)
        except Exception:
            # Column or constraint already exists, ignore
            pass
    # Remove old UNIQUE constraint on device_id and add composite unique constraint
    # This allows multiple users to have the same device_id, but prevents same user from having duplicate device_id
    # MySQL-specific migration code - skip for PostgreSQL
    if DB_TYPE != 'postgresql':
        try:
            # Check if unique_user_device constraint already exists
            cur.execute(f"SHOW INDEX FROM {quote_char}sensors{quote_char} WHERE Key_name = 'unique_user_device'")
            constraint_exists = cur.fetchone() is not None
            cur.fetchall()  # Consume any remaining results
            
            # Check for old unique constraint on device_id alone
            cur.execute(f"SHOW INDEX FROM {quote_char}sensors{quote_char} WHERE Column_name = 'device_id' AND Non_unique = 0 AND Key_name != 'PRIMARY' AND Key_name != 'unique_user_device'")
            old_unique_indexes = cur.fetchall()
            cur.fetchall()  # Consume any remaining results
            
            if old_unique_indexes:
                # Check for foreign keys that depend on device_id
                cur.execute(f"""
                    SELECT CONSTRAINT_NAME, TABLE_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE REFERENCED_TABLE_NAME = '{quote_char}sensors{quote_char}' 
                    AND REFERENCED_COLUMN_NAME = 'device_id'
                    AND TABLE_SCHEMA = DATABASE()
                """)
                fk_refs = cur.fetchall()
                cur.fetchall()  # Consume any remaining results
                
                # Drop foreign keys first if they exist
                for fk in fk_refs:
                    fk_name = fk[0] if isinstance(fk, tuple) else fk.get('CONSTRAINT_NAME')
                    table_name = fk[1] if isinstance(fk, tuple) else fk.get('TABLE_NAME')
                    if fk_name and table_name:
                        # Validate table_name and fk_name contain only safe characters
                        if re.match(r'^[a-zA-Z0-9_]+$', table_name) and re.match(r'^[a-zA-Z0-9_]+$', fk_name):
                            try:
                                cur.execute(f"ALTER TABLE {quote_char}{table_name}{quote_char} DROP FOREIGN KEY {quote_char}{fk_name}{quote_char}")
                                conn.commit()
                                print(f"Dropped foreign key {fk_name} from {table_name} to allow constraint migration")
                            except Exception:
                                pass
                        else:
                            print(f"WARNING: Skipping foreign key drop - unsafe characters in name: {fk_name} or table: {table_name}")
                
                # Drop old unique constraints on device_id
                for idx in old_unique_indexes:
                    idx_name = idx[2] if len(idx) > 2 else None
                    if idx_name:
                        # Validate index name contains only safe characters
                        if re.match(r'^[a-zA-Z0-9_]+$', idx_name):
                            try:
                                cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} DROP INDEX {quote_char}{idx_name}{quote_char}")
                                conn.commit()
                                print(f"Dropped old unique constraint: {idx_name}")
                            except Exception:
                                pass
                        else:
                            print(f"WARNING: Skipping index drop - unsafe characters in name: {idx_name}")
                
                # Recreate device_id as non-unique index (needed for foreign keys)
                try:
                    cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} ADD INDEX idx_sensors_device_id (device_id)")
                    conn.commit()
                except Exception:
                    pass  # Index might already exist
                
                # Recreate foreign keys
                for fk in fk_refs:
                    fk_name = fk[0] if isinstance(fk, tuple) else fk.get('CONSTRAINT_NAME')
                    table_name = fk[1] if isinstance(fk, tuple) else fk.get('TABLE_NAME')
                    if fk_name and table_name:
                        # Validate table_name and fk_name contain only safe characters
                        if re.match(r'^[a-zA-Z0-9_]+$', table_name) and re.match(r'^[a-zA-Z0-9_]+$', fk_name):
                            try:
                                cur.execute(f"""
                                    ALTER TABLE {quote_char}{table_name}{quote_char} 
                                    ADD CONSTRAINT {quote_char}{fk_name}{quote_char} 
                                    FOREIGN KEY (device_id) 
                                    REFERENCES {quote_char}sensors{quote_char}(device_id) 
                                    ON UPDATE CASCADE ON DELETE CASCADE
                                """)
                                conn.commit()
                                print(f"Recreated foreign key {fk_name} on {table_name}")
                            except Exception:
                                pass
                        else:
                            print(f"WARNING: Skipping foreign key recreation - unsafe characters in name: {fk_name} or table: {table_name}")
            
            if not constraint_exists:
                # Add composite unique constraint on (user_id, device_id)
                # This ensures: same user_id + same device_id = NOT allowed
                # But: different user_id + same device_id = ALLOWED
                try:
                    cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} ADD UNIQUE KEY unique_user_device (user_id, device_id)")
                    conn.commit()
                    print("Added composite unique constraint: unique_user_device (user_id, device_id)")
                except Exception as e:
                    # Constraint might already exist
                    print(f"Note: Could not add composite unique constraint: {e}")
                    pass
        except Exception as e:
            # Migration might fail if table structure is different, that's okay
            print(f"Note: Schema migration: {e}")
            pass
    # Per-sensor data time series table (if not already created)
    try:
        if DB_TYPE == 'postgresql':
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {quote_char}sensor_data{quote_char} (
                    id {auto_inc} PRIMARY KEY,
                    sensor_id INT NOT NULL,
                    user_id INT NULL,
                    device_id VARCHAR(100) NULL,
                    recorded_at {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                    value TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'normal' CHECK (status IN ('normal', 'warning', 'critical')),
                    CONSTRAINT fk_sensor_data_sensor FOREIGN KEY (sensor_id)
                        REFERENCES {quote_char}sensors{quote_char}(id) ON UPDATE CASCADE ON DELETE CASCADE
                )
                """
            )
            # Create indexes separately for PostgreSQL
            try:
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_sensor_data_sensor_id ON {quote_char}sensor_data{quote_char}(sensor_id)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_sensor_data_user_id ON {quote_char}sensor_data{quote_char}(user_id)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_sensor_data_device_id ON {quote_char}sensor_data{quote_char}(device_id)")
            except Exception:
                pass
        else:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {quote_char}sensor_data{quote_char} (
                    id {auto_inc} PRIMARY KEY,
                    sensor_id INT NOT NULL,
                    user_id INT NULL,
                    device_id VARCHAR(100) NULL,
                    recorded_at {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                    value TEXT NOT NULL,
                    status ENUM('normal','warning','critical') DEFAULT 'normal',
                    INDEX idx_sensor_data_sensor_id (sensor_id),
                    INDEX idx_sensor_data_user_id (user_id),
                    INDEX idx_sensor_data_device_id (device_id),
                    CONSTRAINT fk_sensor_data_sensor FOREIGN KEY (sensor_id)
                        REFERENCES {quote_char}sensors{quote_char}(id) ON UPDATE CASCADE ON DELETE CASCADE
                )
                """
            )
        # MySQL-specific migration code - skip for PostgreSQL (tables are created fresh)
        if DB_TYPE != 'postgresql':
            # Migrate existing DOUBLE column to TEXT for encryption support
            try:
                cur.execute(f"SHOW COLUMNS FROM {quote_char}sensor_data{quote_char} WHERE Field = 'value' AND Type LIKE 'DOUBLE%'")
                if cur.fetchone():
                    cur.execute(f"ALTER TABLE {quote_char}sensor_data{quote_char} MODIFY COLUMN value TEXT NOT NULL")
                    conn.commit()
                    print("Migrated sensor_data.value column to TEXT for encryption support")
                cur.fetchall()  # Consume any remaining results
            except Exception as e:
                print(f"Note: sensor_data schema migration: {e}")
                try:
                    cur.fetchall()
                except:
                    pass
            
            # Add user_id and device_id columns if they don't exist (migration for existing tables)
            try:
                cur.execute(f"SHOW COLUMNS FROM {quote_char}sensor_data{quote_char} WHERE Field = 'user_id'")
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE {quote_char}sensor_data{quote_char} ADD COLUMN user_id INT NULL AFTER sensor_id")
                    cur.execute(f"ALTER TABLE {quote_char}sensor_data{quote_char} ADD INDEX idx_sensor_data_user_id (user_id)")
                    conn.commit()
                    print("Added user_id column to sensor_data table")
                cur.fetchall()  # Consume any remaining results
            except Exception as e:
                print(f"Note: sensor_data user_id migration: {e}")
                try:
                    cur.fetchall()
                except:
                    pass
            
            try:
                cur.execute(f"SHOW COLUMNS FROM {quote_char}sensor_data{quote_char} WHERE Field = 'device_id'")
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE {quote_char}sensor_data{quote_char} ADD COLUMN device_id VARCHAR(100) NULL AFTER user_id")
                    cur.execute(f"ALTER TABLE {quote_char}sensor_data{quote_char} ADD INDEX idx_sensor_data_device_id (device_id)")
                    conn.commit()
                    print("Added device_id column to sensor_data table")
                cur.fetchall()  # Consume any remaining results
            except Exception as e:
                print(f"Note: sensor_data device_id migration: {e}")
                try:
                    cur.fetchall()
                except:
                    pass
            
            # Backfill user_id and device_id from sensors table for existing records
            try:
                cur.execute(f"""
                    UPDATE {quote_char}sensor_data{quote_char} sd
                    JOIN {quote_char}sensors{quote_char} s ON s.id = sd.sensor_id
                    SET sd.user_id = s.user_id, sd.device_id = s.device_id
                    WHERE sd.user_id IS NULL OR sd.device_id IS NULL
                """)
                rows_updated = cur.rowcount
                if rows_updated > 0:
                    conn.commit()
                    print(f"Backfilled user_id and device_id for {rows_updated} existing sensor_data records")
                cur.fetchall()  # Consume any remaining results
            except Exception as e:
                print(f"Note: sensor_data backfill: {e}")
                try:
                    cur.fetchall()
                except:
                    pass
    except Exception:
        pass
    # MySQL-specific migration code - skip for PostgreSQL (columns already in CREATE TABLE)
    if DB_TYPE != 'postgresql':
        # Ensure legacy schemas allow NULL public_key
        try:
            cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} MODIFY COLUMN public_key TEXT NULL")
        except Exception:
            # Ignore if already NULL or if permissions prevent alter
            pass
        # Note: we no longer drop legacy columns automatically to avoid accidental data loss.
        # Ensure threshold columns exist
        try:
            cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} ADD COLUMN min_threshold {double_type} NULL")
        except Exception:
            pass
        try:
            cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} ADD COLUMN max_threshold {double_type} NULL")
        except Exception:
            pass
        # Ensure sensor_type_id column exists (for FK to sensor_type)
        try:
            cur.execute(f"ALTER TABLE {quote_char}sensors{quote_char} ADD COLUMN sensor_type_id INT NULL")
        except Exception:
            pass
        # Backfill sensor_type_id from device_type where possible
        try:
            cur.execute(
                f"""
                UPDATE {quote_char}sensors{quote_char} s
                JOIN {quote_char}sensor_type{quote_char} st ON st.type_name = s.device_type
                SET s.sensor_type_id = st.id
                WHERE s.sensor_type_id IS NULL
                """
            )
            # Consume any results (UPDATE doesn't return results, but be safe)
            try:
                cur.fetchall()
            except:
                pass
        except Exception:
            # Try to consume results even on error
            try:
                cur.fetchall()
            except:
                pass
        # Add index and FK constraint (best-effort, ignore if exists)
        try:
            cur.execute(f"CREATE INDEX idx_sensors_sensor_type_id ON {quote_char}sensors{quote_char}(sensor_type_id)")
            try:
                cur.fetchall()
            except:
                pass
        except Exception:
            pass
        try:
            cur.execute(
                f"""
                ALTER TABLE {quote_char}sensors{quote_char}
                ADD CONSTRAINT fk_sensors_sensor_type
                FOREIGN KEY (sensor_type_id) REFERENCES {quote_char}sensor_type{quote_char}(id)
                ON UPDATE CASCADE
                ON DELETE SET NULL
                """
            )
            try:
                cur.fetchall()
            except:
                pass
        except Exception:
            pass
    # Device sessions table for secure device-server communication
    if DB_TYPE == 'postgresql':
        # PostgreSQL: Use trigger for ON UPDATE CURRENT_TIMESTAMP
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quote_char}device_sessions{quote_char} (
                id {auto_inc} PRIMARY KEY,
                session_token VARCHAR(255) NOT NULL UNIQUE,
                device_id VARCHAR(100) NOT NULL,
                counter INT DEFAULT 0,
                expires_at {datetime_type} NOT NULL,
                created_at {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                last_used_at {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_device_sessions_device FOREIGN KEY (device_id)
                    REFERENCES {quote_char}sensors{quote_char}(device_id) ON UPDATE CASCADE ON DELETE CASCADE
            )
            """
        )
        # Create indexes separately
        try:
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_device_sessions_token ON {quote_char}device_sessions{quote_char}(session_token)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_device_sessions_device ON {quote_char}device_sessions{quote_char}(device_id)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_device_sessions_expires ON {quote_char}device_sessions{quote_char}(expires_at)")
        except Exception:
            pass
        # Create trigger for last_used_at auto-update (PostgreSQL equivalent of ON UPDATE)
        try:
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_last_used_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.last_used_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            cur.execute("""
                DROP TRIGGER IF EXISTS trigger_update_last_used_at ON device_sessions;
                CREATE TRIGGER trigger_update_last_used_at
                BEFORE UPDATE ON device_sessions
                FOR EACH ROW
                EXECUTE FUNCTION update_last_used_at();
            """)
        except Exception:
            pass
    else:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {quote_char}device_sessions{quote_char} (
                id {auto_inc} PRIMARY KEY,
                session_token VARCHAR(255) NOT NULL UNIQUE,
                device_id VARCHAR(100) NOT NULL,
                counter INT DEFAULT 0,
                expires_at {datetime_type} NOT NULL,
                created_at {datetime_type} DEFAULT CURRENT_TIMESTAMP,
                last_used_at {datetime_type} DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_device_sessions_token (session_token),
                INDEX idx_device_sessions_device (device_id),
                INDEX idx_device_sessions_expires (expires_at),
                CONSTRAINT fk_device_sessions_device FOREIGN KEY (device_id)
                    REFERENCES {quote_char}sensors{quote_char}(device_id) ON UPDATE CASCADE ON DELETE CASCADE
            )
            """
        )
    # Per-user thresholds table removed; using sensor_type defaults and per-sensor overrides
    conn.commit()
    cur.close()


def get_pool():
    global _pool
    if _pool is not None:
        # Test if pool is still valid
        try:
            if DB_TYPE == 'postgresql':
                test_conn = _pool.getconn()
                _pool.putconn(test_conn)
            else:
                test_conn = _pool.get_connection()
                test_conn.close()
            return _pool
        except Exception as e:
            print(f"WARNING: Existing pool is invalid, recreating: {e}")
            _pool = None
    
    print(f"DEBUG: Initializing {DB_TYPE.upper()} database connection pool...")
    print(f"DEBUG: DB_HOST={DB_HOST}, DB_PORT={DB_PORT}, DB_USER={DB_USER}, DB_NAME={DB_NAME}")
    
    if DB_TYPE == 'postgresql':
        if not POSTGRESQL_AVAILABLE:
            print("ERROR: PostgreSQL requested but psycopg2 not available")
            return None
        try:
            _pool = psycopg2.pool.SimpleConnectionPool(
                1,  # min connections
                5,  # max connections
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )
            print("DEBUG: PostgreSQL connection pool created successfully")
            
            # Test the connection
            _conn = _pool.getconn()
            print("DEBUG: Test connection obtained from pool")
            _ensure_schema(_conn)
            _pool.putconn(_conn)
            print("DEBUG: PostgreSQL database connection pool initialized successfully")
            return _pool
        except Exception as e:
            _pool = None
            print(f"ERROR: PostgreSQL connection error: {e}")
            import traceback
            traceback.print_exc()
            return None
    else:
        # MySQL connection
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="water_pool",
                pool_size=5,
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )
            print("DEBUG: MySQL connection pool created successfully")
            
            # Test the connection
            _conn = _pool.get_connection()
            print("DEBUG: Test connection obtained from pool")
            _ensure_schema(_conn)
            _conn.close()
            print("DEBUG: MySQL database connection pool initialized successfully")
            return _pool
        except Error as init_err:
            errno = getattr(init_err, 'errno', None)
            print(f"ERROR: MySQL connection error (errno: {errno}): {init_err}")
            import traceback
            traceback.print_exc()
            
            if errno == errorcode.ER_BAD_DB_ERROR:
                print("DEBUG: Database does not exist, attempting to create...")
                _create_database_if_missing()
                try:
                    _pool = pooling.MySQLConnectionPool(
                        pool_name="water_pool",
                        pool_size=5,
                        host=DB_HOST,
                        port=DB_PORT,
                        user=DB_USER,
                        password=DB_PASSWORD,
                        database=DB_NAME,
                    )
                    _conn = _pool.get_connection()
                    _ensure_schema(_conn)
                    _return_connection(_pool, _conn)
                    print("DEBUG: Database created and connection pool initialized")
                    return _pool
                except Exception as retry_err:
                    _pool = None
                    print(f"ERROR: MySQL init retry failed: {retry_err}")
                    import traceback
                    traceback.print_exc()
            else:
                _pool = None
                print(f"ERROR: MySQL init failed: {init_err}")
                print(f"ERROR: Check MySQL server is running and credentials are correct")
        except Exception as e:
            _pool = None
            print(f"ERROR: Unexpected error initializing database pool: {e}")
            import traceback
            traceback.print_exc()
        
        return _pool


def insert_reading(tds: float, ph: float, turbidity: float, safe: bool, reasons) -> None:
    pool = get_pool()
    if pool is None:
        return
    try:
        # Encrypt sensor values before storing
        encryption = get_db_encryption()
        encrypted_tds = encryption.encrypt_value(tds)
        encrypted_ph = encryption.encrypt_value(ph)
        encrypted_turbidity = encryption.encrypt_value(turbidity)
        
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            INSERT INTO water_readings (tds, ph, turbidity, safe_to_drink, safety_issues)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                encrypted_tds,
                encrypted_ph,
                encrypted_turbidity,
                1 if safe else 0,
                json.dumps(reasons) if reasons else None,
            ),
        )
        conn.commit()
        cur.close()
        _return_connection(pool, conn)
    except Exception as db_err:
        print(f"MySQL write error: {db_err}")



def create_user(email: str, name: str, username: str, password_hash: str) -> bool:
    pool = get_pool()
    if pool is None:
        print("ERROR: Database connection pool is None in create_user()")
        print("ERROR: Cannot create user - database not connected")
        return False
    try:
        # Verify password hash format before storing
        if not password_hash or len(password_hash) < 10:
            print(f"ERROR: Invalid password hash format - length: {len(password_hash) if password_hash else 0}")
            return False
        
        print(f"DEBUG: Attempting to create user - email: '{email}', username: '{username}'")
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        
        # Check if username or email already exists first
        cur.execute("SELECT username, email FROM user_cred WHERE username = %s OR email = %s LIMIT 2", (username, email))
        existing = cur.fetchall()
        if existing:
            for row in existing:
                existing_username = row[0] if isinstance(row, tuple) else row.get('username')
                existing_email = row[1] if isinstance(row, tuple) else row.get('email')
                if existing_username == username:
                    print(f"DEBUG: Username already exists: '{username}'")
                if existing_email == email:
                    print(f"DEBUG: Email already exists: '{email}'")
            cur.close()
            _return_connection(pool, conn)
            return False
        
        cur.execute(
            """
            INSERT INTO user_cred (email, name, username, password)
            VALUES (%s, %s, %s, %s)
            """,
            (email, name, username, password_hash),
        )
        conn.commit()
        print(f"DEBUG: User created successfully - username: '{username}'")
        
        # Verify the password was stored correctly
        cur.execute("SELECT password FROM user_cred WHERE username = %s LIMIT 1", (username,))
        stored = cur.fetchone()
        if stored:
            stored_hash = stored[0] if isinstance(stored, tuple) else stored.get('password')
            if stored_hash != password_hash:
                print(f"WARNING: Password hash mismatch! Stored: {len(stored_hash) if stored_hash else 0} chars, Expected: {len(password_hash)} chars")
            else:
                print(f"DEBUG: Password hash stored correctly - {len(stored_hash)} chars")
        
        cur.close()
        _return_connection(pool, conn)
        return True
    except Error as e:
        errno = getattr(e, 'errno', None)
        msg = str(e)
        print(f"ERROR: MySQL create_user error (errno: {errno}): {msg}")
        
        # Duplicate username or email
        if errno == errorcode.ER_DUP_ENTRY:
            if 'username' in msg.lower():
                print(f"DEBUG: Duplicate username: '{username}'")
            elif 'email' in msg.lower():
                print(f"DEBUG: Duplicate email: '{email}'")
            else:
                print(f"DEBUG: Duplicate entry (username or email)")
            return False
        
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error in create_user: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_user_by_username(username: str):
    pool = get_pool()
    if pool is None:
        print("ERROR: Database connection pool is None in get_user_by_username()")
        return None
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        # Try exact match first, then case-insensitive
        cur.execute(
            """
            SELECT sr_no, email, name, username, password
            FROM user_cred
            WHERE username = %s
            LIMIT 1
            """,
            (username,),
        )
        row = cur.fetchone()
        
        # If not found, try case-insensitive search
        if not row:
            cur.execute(
                """
                SELECT sr_no, email, name, username, password
                FROM user_cred
                WHERE LOWER(username) = LOWER(%s)
                LIMIT 1
                """,
                (username,),
            )
            row = cur.fetchone()
        
        cur.close()
        _return_connection(pool, conn)
        if row:
            print(f"DEBUG: Found user: {row.get('username')} (searched for: {username})")
            print(f"DEBUG: User data - sr_no: {row.get('sr_no')}, email: {row.get('email')}")
        else:
            print(f"DEBUG: User not found: {username}")
        return row
    except Exception as e:
        print(f"ERROR: MySQL get_user_by_username error: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_user_by_email(email: str):
    pool = get_pool()
    if pool is None:
        return None
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        cur.execute(
            """
            SELECT sr_no, email, name, username, password
            FROM user_cred
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )
        row = cur.fetchone()
        cur.close()
        _return_connection(pool, conn)
        return row
    except Exception as e:
        print(f"MySQL get_user_by_email error: {e}")
        return None



def update_user_profile(current_username: str, new_email: str, new_name: str, new_username: str) -> bool:
    pool = get_pool()
    if pool is None:
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            UPDATE user_cred
            SET email = %s, name = %s, username = %s
            WHERE username = %s
            """,
            (new_email, new_name, new_username, current_username),
        )
        conn.commit()
        updated = cur.rowcount > 0
        cur.close()
        _return_connection(pool, conn)
        return updated
    except Error as e:
        # Duplicate key (email or username)
        if getattr(e, 'errno', None) == errorcode.ER_DUP_ENTRY:
            return False
        print(f"MySQL update_user_profile error: {e}")
        return False


def update_user_password(username: str, password_hash: str) -> bool:
    pool = get_pool()
    if pool is None:
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            UPDATE user_cred
            SET password = %s
            WHERE username = %s
            """,
            (password_hash, username),
        )
        conn.commit()
        updated = cur.rowcount > 0
        cur.close()
        _return_connection(pool, conn)
        return updated
    except Exception as e:
        print(f"MySQL update_user_password error: {e}")
        return False


def create_sensor(
    device_id: str,
    device_type: str,
    location: str | None,
    public_key: str | None,
    status: str = 'active',
    user_id: int | None = None,
) -> bool:
    pool = get_pool()
    if pool is None:
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        # Resolve sensor_type_id from sensor_type table
        cur.execute(
            """
            SELECT id FROM `sensor_type` WHERE type_name = %s LIMIT 1
            """,
            (device_type,)
        )
        row = cur.fetchone()
        sensor_type_id = row[0] if row else None
        cur.execute(
            """
            INSERT INTO sensors (
                device_id, device_type, sensor_type_id, location, public_key, status, user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                device_id,
                device_type,
                sensor_type_id,
                location,
                public_key,
                status,
                user_id,
            ),
        )
        conn.commit()
        cur.close()
        _return_connection(pool, conn)
        return True
    except Error as e:
        if getattr(e, 'errno', None) == errorcode.ER_DUP_ENTRY:
            # This is a duplicate (user_id, device_id) combination
            # The composite unique constraint unique_user_device prevents same user from registering same device_id twice
            print(f"MySQL create_sensor: duplicate (user_id={user_id}, device_id='{device_id}') - this user already has this device_id")
            return False
        print(f"MySQL create_sensor error: {e}")
        return False


def get_sensor_by_device_id(device_id: str, user_id: int | None = None):
    pool = get_pool()
    if pool is None:
        return None
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        if user_id is not None:
            cur.execute(
                """
                SELECT * FROM sensors WHERE device_id = %s AND user_id = %s LIMIT 1
                """,
                (device_id, int(user_id)),
            )
        else:
            cur.execute(
                """
                SELECT * FROM sensors WHERE device_id = %s LIMIT 1
                """,
                (device_id,),
            )
        row = cur.fetchone()
        cur.close()
        _return_connection(pool, conn)
        return row
    except Exception as e:
        print(f"MySQL get_sensor_by_device_id error: {e}")
        return None

def update_sensor_by_device_id(
    device_id: str,
    location: str | None,
    status: str,
    public_key: str | None,
    min_threshold: float | None,
    max_threshold: float | None,
) -> bool:
    pool = get_pool()
    if pool is None:
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            UPDATE sensors
            SET location = %s,
                status = %s,
                public_key = %s,
                min_threshold = %s,
                max_threshold = %s
            WHERE device_id = %s
            """,
            (
                location,
                status,
                public_key,
                None if min_threshold is None else float(min_threshold),
                None if max_threshold is None else float(max_threshold),
                device_id,
            ),
        )
        conn.commit()
        updated = cur.rowcount > 0
        cur.close()
        _return_connection(pool, conn)
        return updated
    except Exception as e:
        print(f"MySQL update_sensor_by_device_id error: {e}")
        return False

def list_sensors(limit: int | None = None, user_id: int | None = None):
    pool = get_pool()
    if pool is None:
        return []
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        if user_id is not None:
            if limit is not None:
                cur.execute(
                    """
                    SELECT * FROM sensors
                    WHERE user_id = %s
                    ORDER BY registered_at DESC
                    LIMIT %s
                    """,
                    (int(user_id), int(limit)),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM sensors
                    WHERE user_id = %s
                    ORDER BY registered_at DESC
                    """,
                    (int(user_id),),
                )
        else:
            if limit is not None:
                cur.execute(
                    """
                    SELECT * FROM sensors
                    ORDER BY registered_at DESC
                    LIMIT %s
                    """,
                    (int(limit),),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM sensors
                    ORDER BY registered_at DESC
                    """
                )
        rows = cur.fetchall()
        cur.close()
        _return_connection(pool, conn)
        return rows or []
    except Exception as e:
        print(f"MySQL list_sensors error: {e}")
        return []

def count_active_sensors(exclude_device_id: str | None = None) -> int:
    pool = get_pool()
    if pool is None:
        return 0
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        if exclude_device_id:
            cur.execute(
                """
                SELECT COUNT(*) FROM sensors
                WHERE status = 'active' AND device_id <> %s
                """,
                (exclude_device_id,),
            )
        else:
            cur.execute(
                """
                SELECT COUNT(*) FROM sensors
                WHERE status = 'active'
                """
            )
        row = cur.fetchone()
        cur.close()
        _return_connection(pool, conn)
        return int(row[0] if row and row[0] is not None else 0)
    except Exception as e:
        print(f"MySQL count_active_sensors error: {e}")
        return 0

def count_active_sensors_by_location(location: str | None, exclude_device_id: str | None = None, user_id: int | None = None) -> int:
    pool = get_pool()
    if pool is None:
        return 0
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        normalized_location = (location or '').strip()
        if user_id is not None:
            if exclude_device_id:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM sensors
                    WHERE status = 'active'
                      AND user_id = %s
                      AND LOWER(COALESCE(TRIM(location), '')) = LOWER(%s)
                      AND device_id <> %s
                    """,
                    (int(user_id), normalized_location, exclude_device_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM sensors
                    WHERE status = 'active'
                      AND user_id = %s
                      AND LOWER(COALESCE(TRIM(location), '')) = LOWER(%s)
                    """,
                    (int(user_id), normalized_location,),
                )
        else:
            if exclude_device_id:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM sensors
                    WHERE status = 'active'
                      AND LOWER(COALESCE(TRIM(location), '')) = LOWER(%s)
                      AND device_id <> %s
                    """,
                    (normalized_location, exclude_device_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM sensors
                    WHERE status = 'active'
                      AND LOWER(COALESCE(TRIM(location), '')) = LOWER(%s)
                    """,
                    (normalized_location,),
                )
        row = cur.fetchone()
        cur.close()
        _return_connection(pool, conn)
        return int(row[0] if row and row[0] is not None else 0)
    except Exception as e:
        print(f"MySQL count_active_sensors_by_location error: {e}")
        return 0

def delete_sensor_by_device_id(device_id: str) -> bool:
    pool = get_pool()
    if pool is None:
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            DELETE FROM sensors WHERE device_id = %s
            """,
            (device_id,),
        )
        conn.commit()
        deleted = cur.rowcount > 0
        cur.close()
        _return_connection(pool, conn)
        return deleted
    except Exception as e:
        print(f"MySQL delete_sensor_by_device_id error: {e}")
        return False
    
def seed_sensor_types_if_empty():
    """Manually seed sensor types if the table is empty. Returns True if seeded, False otherwise."""
    pool = get_pool()
    if pool is None:
        print("ERROR: Database connection pool is None in seed_sensor_types_if_empty()")
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute("SELECT COUNT(*) FROM `sensor_type`")
        row = cur.fetchone()
        count = int(row[0]) if row and row[0] is not None else 0
        if count == 0:
            print("Seeding default sensor types (manual call)...")
            cur.executemany(
                """
                INSERT INTO sensor_type (type_name, unit, default_min, default_max, description)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [
                    ("ph", None, 6.5, 8.5, "pH level"),
                    ("tds", "ppm", 0.0, 500.0, "Total Dissolved Solids"),
                    ("turbidity", "NTU", 0.0, 5.0, "Turbidity"),
                ],
            )
            conn.commit()
            cur.close()
            _return_connection(pool, conn)
            print("Successfully seeded default sensor types")
            return True
        else:
            cur.close()
            _return_connection(pool, conn)
            print(f"sensor_type table already has {count} entries")
            return False
    except Exception as e:
        print(f"ERROR: Failed to seed sensor types: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_sensor_types():
    pool = get_pool()
    if pool is None:
        print("ERROR: Database connection pool is None in list_sensor_types()")
        return []
    
    conn = None
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        
        # Simple, direct query
        cur.execute("SELECT id, type_name, unit, default_min, default_max, description FROM `sensor_type` ORDER BY type_name ASC")
        rows = cur.fetchall()
        
        # Convert to list and ensure it's not None
        if rows is None:
            rows = []
        
        # Ensure each row is a dict with proper keys
        result = []
        for row in rows:
            if isinstance(row, dict):
                result.append(row)
            else:
                # Convert tuple to dict if needed
                result.append({
                    'id': row[0] if len(row) > 0 else None,
                    'type_name': row[1] if len(row) > 1 else None,
                    'unit': row[2] if len(row) > 2 else None,
                    'default_min': row[3] if len(row) > 3 else None,
                    'default_max': row[4] if len(row) > 4 else None,
                    'description': row[5] if len(row) > 5 else None,
                })
        
        cur.close()
        _return_connection(pool, conn)
        
        print(f"DEBUG: list_sensor_types() returning {len(result)} sensor types")
        if result:
            print(f"DEBUG: Sensor types: {[r.get('type_name', 'NO_NAME') for r in result]}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: MySQL list_sensor_types error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            try:
                _return_connection(pool, conn)
            except:
                pass
        # Return empty list on error
        return []

def insert_sensor_data(sensor_db_id: int, value: float, status: str = 'normal', user_id: int | None = None, device_id: str | None = None) -> bool:
    pool = get_pool()
    if pool is None:
        print("ERROR: insert_sensor_data - Database pool is None")
        return False
    
    if sensor_db_id is None:
        print(f"ERROR: insert_sensor_data - sensor_db_id is None")
        return False
    
    if value is None:
        print(f"WARNING: insert_sensor_data - value is None for sensor_db_id: {sensor_db_id}")
        return False
    
    try:
        # Encrypt sensor value before storing
        encryption = get_db_encryption()
        encrypted_value = encryption.encrypt_value(value)
        
        if encrypted_value is None:
            print(f"ERROR: insert_sensor_data - encryption returned None for value: {value}")
            return False
        
        conn = pool.get_connection()
        
        # If user_id or device_id not provided, fetch from sensors table
        if user_id is None or device_id is None:
            cur_select = conn.cursor(dictionary=True)
            cur_select.execute(
                "SELECT user_id, device_id FROM sensors WHERE id = %s LIMIT 1",
                (int(sensor_db_id),)
            )
            sensor_row = cur_select.fetchone()
            cur_select.close()
            if sensor_row:
                if user_id is None:
                    user_id = sensor_row.get('user_id')
                if device_id is None:
                    device_id = sensor_row.get('device_id')
        
        cur = conn.cursor()
        
        cur.execute(
            """
            INSERT INTO sensor_data (sensor_id, user_id, device_id, value, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (int(sensor_db_id), user_id, device_id, encrypted_value, status or 'normal'),
        )
        conn.commit()
        rows_affected = cur.rowcount
        cur.close()
        _return_connection(pool, conn)
        
        if rows_affected > 0:
            import sys
            msg = f"DEBUG: insert_sensor_data - Successfully inserted row for sensor_db_id: {sensor_db_id}, value: {value}\n"
            print(msg, file=sys.stderr)
            sys.stderr.flush()
            return True
        else:
            import sys
            msg = f"WARNING: insert_sensor_data - No rows affected for sensor_db_id: {sensor_db_id}\n"
            print(msg, file=sys.stderr)
            sys.stderr.flush()
            return False
    except Exception as e:
        import sys
        import traceback
        msg = f"ERROR: MySQL insert_sensor_data error for sensor_db_id {sensor_db_id}: {e}\n"
        msg += traceback.format_exc()
        print(msg, file=sys.stderr)
        sys.stderr.flush()
        return False


def get_sensor_type_by_type(sensor_type: str):
    pool = get_pool()
    if pool is None:
        return None
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        cur.execute(
            """
            SELECT id, type_name, unit, default_min, default_max, description
            FROM `sensor_type`
            WHERE LOWER(type_name) = LOWER(%s)
            LIMIT 1
            """,
            (sensor_type,),
        )
        row = cur.fetchone()
        cur.close()
        _return_connection(pool, conn)
        return row
    except Exception as e:
        print(f"MySQL get_sensor_type_by_type error: {e}")
        return None
    
def get_thresholds_by_user(user_id: int):
    # Deprecated
    return {}


def get_threshold_for_user(user_id: int, sensor_type: str):
    # Deprecated
    return None


def upsert_threshold(user_id: int, sensor_type: str, min_value, max_value, use_default: bool) -> bool:
    # Deprecated
    return False

def list_recent_sensor_data(limit: int = 100, user_id: int | None = None):
    pool = get_pool()
    if pool is None:
        return []
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        if user_id is not None:
            # Use user_id directly from sensor_data table (no JOIN needed)
            cur.execute(
                """
                SELECT 
                    sd.id,
                    sd.sensor_id AS sensor_db_id,
                    sd.user_id,
                    sd.device_id,
                    sd.recorded_at,
                    sd.value,
                    sd.status,
                    s.device_type,
                    s.location
                FROM sensor_data sd
                LEFT JOIN sensors s ON s.id = sd.sensor_id
                WHERE sd.user_id = %s
                ORDER BY sd.recorded_at DESC, sd.id DESC
                LIMIT %s
                """,
                (int(user_id), int(limit)),
            )
        else:
            # No user filter - get all data
            cur.execute(
                """
                SELECT 
                    sd.id,
                    sd.sensor_id AS sensor_db_id,
                    sd.user_id,
                    sd.device_id,
                    sd.recorded_at,
                    sd.value,
                    sd.status,
                    s.device_type,
                    s.location
                FROM sensor_data sd
                LEFT JOIN sensors s ON s.id = sd.sensor_id
                ORDER BY sd.recorded_at DESC, sd.id DESC
                LIMIT %s
                """,
                (int(limit),),
            )
        rows = cur.fetchall() or []
        cur.close()
        _return_connection(pool, conn)
        
        # Decrypt sensor values after retrieving from database
        import sys
        print(f"DEBUG: list_recent_sensor_data - Retrieved {len(rows)} rows from database", file=sys.stderr)
        sys.stderr.flush()
        
        encryption = get_db_encryption()
        decrypted_rows = []
        for row in rows:
            decrypted_row = row.copy()
            encrypted_value = row.get('value')
            decrypted_value = encryption.decrypt_value(encrypted_value)
            decrypted_row['value'] = decrypted_value
            
            if decrypted_value is None:
                print(f"WARNING: list_recent_sensor_data - Decryption returned None for row id={row.get('id')}, device_id={row.get('device_id')}, encrypted_value={encrypted_value[:50] if encrypted_value else 'None'}...", file=sys.stderr)
                sys.stderr.flush()
            
            decrypted_rows.append(decrypted_row)
        
        print(f"DEBUG: list_recent_sensor_data - Returning {len(decrypted_rows)} decrypted rows", file=sys.stderr)
        sys.stderr.flush()
        return decrypted_rows
    except Exception as e:
        print(f"MySQL list_recent_sensor_data error: {e}")
        return []

def get_locations_with_status(user_id: int | None = None, realtime_metrics_data: dict | None = None):
    """Get all locations with their latest safety status and sensor count.
    
    Args:
        user_id: User ID to filter locations
        realtime_metrics_data: Optional dict of {metric_name: {'value': val, 'sensor_id': device_id}} from real-time data
    """
    pool = get_pool()
    if pool is None:
        return []
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        
        if user_id is not None:
            # Get all locations for this user's sensors, including NULL (will show as "Unassigned")
            cur.execute("""
                SELECT DISTINCT COALESCE(s.location, 'Unassigned') as location
                FROM sensors s
                WHERE s.user_id = %s
                ORDER BY CASE WHEN s.location IS NULL THEN 1 ELSE 0 END, s.location
            """, (int(user_id),))
        else:
            cur.execute("""
                SELECT DISTINCT COALESCE(s.location, 'Unassigned') as location
                FROM sensors s
                ORDER BY CASE WHEN s.location IS NULL THEN 1 ELSE 0 END, s.location
            """)
        
        locations = [row['location'] for row in cur.fetchall()]
        cur.close()
        _return_connection(pool, conn)
        
        import sys
        print(f"DEBUG: get_locations_with_status - Found {len(locations)} locations for user_id {user_id}", file=sys.stderr)
        if locations:
            print(f"DEBUG: get_locations_with_status - Locations: {locations}", file=sys.stderr)
        else:
            print(f"WARNING: get_locations_with_status - No locations found for user_id {user_id}", file=sys.stderr)
            # Check if user has any sensors at all
            conn_check = pool.get_connection()
            cur_check = conn_check.cursor(dictionary=True)
            if user_id is not None:
                cur_check.execute("SELECT COUNT(*) as count FROM sensors WHERE user_id = %s", (int(user_id),))
            else:
                cur_check.execute("SELECT COUNT(*) as count FROM sensors")
            sensor_count = cur_check.fetchone()['count']
            cur_check.close()
            conn_check.close()
            print(f"DEBUG: get_locations_with_status - User {user_id} has {sensor_count} total sensors", file=sys.stderr)
            if sensor_count > 0:
                # Check if sensors have NULL location
                conn_check2 = pool.get_connection()
                cur_check2 = conn_check2.cursor(dictionary=True)
                if user_id is not None:
                    cur_check2.execute("SELECT COUNT(*) as count FROM sensors WHERE user_id = %s AND (location IS NULL OR location = '')", (int(user_id),))
                else:
                    cur_check2.execute("SELECT COUNT(*) as count FROM sensors WHERE location IS NULL OR location = ''")
                null_location_count = cur_check2.fetchone()['count']
                cur_check2.close()
                conn_check2.close()
                print(f"DEBUG: get_locations_with_status - User {user_id} has {null_location_count} sensors with NULL/empty location", file=sys.stderr)
                # If all sensors have NULL location, show "Unassigned"
                if null_location_count == sensor_count:
                    locations = ['Unassigned']
                    print(f"DEBUG: get_locations_with_status - All sensors have NULL location, adding 'Unassigned'", file=sys.stderr)
        sys.stderr.flush()
        
        # Get safety status for each location
        result = []
        # Build default thresholds map (fallback)
        default_thresholds = {}
        try:
            for t in list_sensor_types() or []:
                type_name = (t.get('type_name') or '').lower()
                default_thresholds[type_name] = {
                    'min': t.get('default_min'),
                    'max': t.get('default_max'),
                }
        except Exception:
            pass
        
        # Get sensors by location for filtering real-time data
        sensors_by_location = {}
        if user_id is not None:
            conn_sensors = pool.get_connection()
            cur_sensors = conn_sensors.cursor(dictionary=True)
            cur_sensors.execute("""
                SELECT device_id, device_type, location
                FROM sensors
                WHERE user_id = %s AND status = 'active'
            """, (int(user_id),))
            all_user_sensors = cur_sensors.fetchall()
            cur_sensors.close()
            conn_sensors.close()
            
            for sensor in all_user_sensors:
                sensor_location = sensor.get('location') or 'Unassigned'
                if sensor_location not in sensors_by_location:
                    sensors_by_location[sensor_location] = []
                sensors_by_location[sensor_location].append({
                    'device_id': sensor.get('device_id'),
                    'device_type': (sensor.get('device_type') or '').lower()
                })
        
        for location in locations:
            # Get latest readings for this location
            # Handle "Unassigned" location (NULL in database)
            location_filter = None if location == 'Unassigned' else location
            
            # Filter real-time metrics for this specific location
            location_realtime_metrics = None
            if realtime_metrics_data and location in sensors_by_location:
                location_realtime_metrics = {}
                location_sensor_ids = {s['device_id'] for s in sensors_by_location[location]}
                # Map from metric_name->{sensor_id, value} to device_type->value for this location
                for metric_name, entry in realtime_metrics_data.items():
                    if not entry:
                        continue
                    sid = entry.get('sensor_id')
                    if sid and sid in location_sensor_ids:
                        try:
                            # Find sensor in location's sensors to get device_type
                            for loc_sensor in sensors_by_location[location]:
                                if loc_sensor['device_id'] == sid:
                                    device_type = loc_sensor['device_type']
                                    if device_type:
                                        val = entry.get('value')
                                        if val is not None:
                                            location_realtime_metrics[device_type] = float(val)
                                    break
                        except Exception:
                            pass
                
                import sys
                if location_realtime_metrics:
                    print(f"DEBUG: get_locations_with_status - Location '{location}' has real-time metrics: {location_realtime_metrics}", file=sys.stderr)
                else:
                    print(f"DEBUG: get_locations_with_status - Location '{location}' has no real-time metrics (sensors: {location_sensor_ids})", file=sys.stderr)
                sys.stderr.flush()
            
            if user_id is not None:
                conn = pool.get_connection()
                cur = conn.cursor(dictionary=True)
                # IMPORTANT: Filter by BOTH sensor.user_id AND sensor_data.user_id
                # This ensures only data from sensors owned by this user is shown
                if location_filter:
                    cur.execute("""
                        SELECT sd.value, s.device_type, sd.recorded_at, s.user_id as sensor_user_id, sd.user_id as data_user_id
                        FROM sensor_data sd
                        JOIN sensors s ON s.id = sd.sensor_id
                        WHERE s.location = %s 
                        AND s.user_id = %s 
                        AND sd.user_id = %s
                        ORDER BY sd.recorded_at DESC
                        LIMIT 100
                    """, (location_filter, int(user_id), int(user_id)))
                else:
                    # Handle "Unassigned" - sensors with NULL/empty location
                    cur.execute("""
                        SELECT sd.value, s.device_type, sd.recorded_at, s.user_id as sensor_user_id, sd.user_id as data_user_id
                        FROM sensor_data sd
                        JOIN sensors s ON s.id = sd.sensor_id
                        WHERE (s.location IS NULL OR s.location = '')
                        AND s.user_id = %s 
                        AND sd.user_id = %s
                        ORDER BY sd.recorded_at DESC
                        LIMIT 100
                    """, (int(user_id), int(user_id)))
            else:
                conn = pool.get_connection()
                cur = conn.cursor(dictionary=True)
                if location_filter:
                    cur.execute("""
                        SELECT sd.value, s.device_type, sd.recorded_at
                        FROM sensor_data sd
                        JOIN sensors s ON s.id = sd.sensor_id
                        WHERE s.location = %s
                        ORDER BY sd.recorded_at DESC
                        LIMIT 100
                    """, (location_filter,))
                else:
                    # Handle "Unassigned" - sensors with NULL/empty location
                    cur.execute("""
                        SELECT sd.value, s.device_type, sd.recorded_at
                        FROM sensor_data sd
                        JOIN sensors s ON s.id = sd.sensor_id
                        WHERE (s.location IS NULL OR s.location = '')
                        ORDER BY sd.recorded_at DESC
                        LIMIT 100
                    """)
            
            rows = cur.fetchall()
            cur.close()
            _return_connection(pool, conn)
            
            # Get latest metrics - prefer real-time data if available, otherwise use stored data
            encryption = get_db_encryption()
            latest_metrics = {}
            
            # First, use real-time data if provided (most up-to-date) - use location-specific if available
            if location_realtime_metrics:
                for device_type, value in location_realtime_metrics.items():
                    device_type_lower = device_type.lower() if isinstance(device_type, str) else str(device_type).lower()
                    if value is not None:
                        try:
                            latest_metrics[device_type_lower] = float(value)
                            import sys
                            print(f"DEBUG: get_locations_with_status - Using real-time {device_type_lower}={value} for location '{location}'", file=sys.stderr)
                            sys.stderr.flush()
                        except (ValueError, TypeError):
                            pass
            
            # Then, fill in missing metrics from stored data
            # Track the most recent timestamp per device_type
            device_type_timestamps = {}
            for row in rows:
                device_type = (row.get('device_type') or '').lower()
                if not device_type:
                    continue
                # Skip if we already have real-time data for this device_type
                if device_type in latest_metrics:
                    continue
                recorded_at = row.get('recorded_at')
                # If we haven't seen this device_type, or this reading is more recent, use it
                if device_type not in latest_metrics or (recorded_at and device_type_timestamps.get(device_type) and recorded_at > device_type_timestamps.get(device_type)):
                    decrypted_value = encryption.decrypt_value(row.get('value'))
                    if decrypted_value is not None:
                        latest_metrics[device_type] = decrypted_value
                        if recorded_at:
                            device_type_timestamps[device_type] = recorded_at
            
            # Calculate safety using sensor-specific thresholds if available, otherwise defaults
            # Build effective thresholds for each device_type in this location
            effective_thresholds = {}
            for device_type, val in latest_metrics.items():
                # Try to find a sensor of this type in this location to get its thresholds
                sensor_with_type = None
                if location in sensors_by_location:
                    for loc_sensor in sensors_by_location[location]:
                        if loc_sensor['device_type'] == device_type:
                            try:
                                # Import here to avoid circular dependency
                                from app import build_effective_thresholds_for_sensor
                                sensor_thresholds = build_effective_thresholds_for_sensor(loc_sensor['device_id'])
                                if sensor_thresholds and device_type in sensor_thresholds:
                                    effective_thresholds[device_type] = sensor_thresholds[device_type]
                                    break
                            except Exception:
                                pass
                
                # Fallback to default if no sensor-specific threshold found
                if device_type not in effective_thresholds and device_type in default_thresholds:
                    effective_thresholds[device_type] = default_thresholds[device_type]
            
            safe = True
            reasons = []
            for key, val in latest_metrics.items():
                if key not in effective_thresholds:
                    continue
                th = effective_thresholds.get(key) or {}
                min_v = th.get('min')
                max_v = th.get('max')
                if min_v is not None and val < min_v:
                    safe = False
                    reasons.append(f"{key} below minimum: {val} < {min_v}")
                elif max_v is not None and val > max_v:
                    safe = False
                    reasons.append(f"{key} above maximum: {val} > {max_v}")
            
            # Count sensors in this location
            conn = pool.get_connection()
            cur = conn.cursor(dictionary=True)
            location_filter = None if location == 'Unassigned' else location
            
            if user_id is not None:
                if location_filter:
                    cur.execute("""
                        SELECT COUNT(DISTINCT s.id) as sensor_count
                        FROM sensors s
                        WHERE s.location = %s AND s.user_id = %s AND s.status = 'active'
                    """, (location_filter, int(user_id)))
                else:
                    # Count sensors with NULL/empty location
                    cur.execute("""
                        SELECT COUNT(DISTINCT s.id) as sensor_count
                        FROM sensors s
                        WHERE (s.location IS NULL OR s.location = '') AND s.user_id = %s AND s.status = 'active'
                    """, (int(user_id),))
            else:
                if location_filter:
                    cur.execute("""
                        SELECT COUNT(DISTINCT s.id) as sensor_count
                        FROM sensors s
                        WHERE s.location = %s AND s.status = 'active'
                    """, (location_filter,))
                else:
                    cur.execute("""
                        SELECT COUNT(DISTINCT s.id) as sensor_count
                        FROM sensors s
                        WHERE (s.location IS NULL OR s.location = '') AND s.status = 'active'
                    """)
            sensor_count_row = cur.fetchone()
            sensor_count = sensor_count_row['sensor_count'] if sensor_count_row else 0
            cur.close()
            _return_connection(pool, conn)
            
            result.append({
                'location': location,
                'sensor_count': sensor_count,
                'safe': safe,
                'reasons': reasons,
                'latest_metrics': latest_metrics
            })
        
        return result
    except Exception as e:
        print(f"MySQL get_locations_with_status error: {e}")
        import traceback
        traceback.print_exc()
        return []

def list_recent_sensor_data_by_location(location: str, limit: int = 200, user_id: int | None = None, date_from=None, date_to=None):
    """Get sensor data filtered by location and optional date range."""
    # Handle "Unassigned" location (NULL in database)
    location_filter = None if location == 'Unassigned' else location
    
    pool = get_pool()
    if pool is None:
        return []
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        
        # Build WHERE clause with date filtering
        where_clauses = []
        params = []
        
        if location_filter:
            where_clauses.append("s.location = %s")
            params.append(location_filter)
        else:
            where_clauses.append("(s.location IS NULL OR s.location = '')")
        
        if user_id is not None:
            where_clauses.append("s.user_id = %s")
            params.append(int(user_id))
            where_clauses.append("sd.user_id = %s")
            params.append(int(user_id))
        
        if date_from:
            where_clauses.append("sd.recorded_at >= %s")
            params.append(date_from)
        if date_to:
            # Use < instead of <= to avoid timezone issues, or add time to end of day
            # If date_to is just a date (no time), add end of day time
            if isinstance(date_to, datetime) and date_to.hour == 0 and date_to.minute == 0 and date_to.second == 0:
                # It's just a date, so include the entire day
                from datetime import timedelta
                date_to_end = date_to + timedelta(days=1) - timedelta(seconds=1)
                where_clauses.append("sd.recorded_at < %s")
                params.append(date_to_end)
            else:
                where_clauses.append("sd.recorded_at <= %s")
                params.append(date_to)
        
        where_sql = " AND ".join(where_clauses)
        params.append(int(limit))
        
        query = f"""
            SELECT 
                sd.id,
                sd.sensor_id AS sensor_db_id,
                sd.user_id,
                sd.device_id,
                sd.recorded_at,
                sd.value,
                sd.status,
                s.device_type,
                s.location
            FROM sensor_data sd
            LEFT JOIN sensors s ON s.id = sd.sensor_id
            WHERE {where_sql}
            ORDER BY sd.recorded_at DESC, sd.id DESC
            LIMIT %s
        """
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall() or []
        cur.close()
        _return_connection(pool, conn)
        
        # Decrypt sensor values after retrieving from database
        import sys
        encryption = get_db_encryption()
        decrypted_rows = []
        for row in rows:
            # SECURITY CHECK: Verify user_id matches (double-check filtering)
            if user_id is not None:
                row_user_id = row.get('user_id')
                if row_user_id != user_id:
                    print(f"WARNING: list_recent_sensor_data_by_location - Row has user_id {row_user_id} but expected {user_id} - SKIPPING", file=sys.stderr)
                    sys.stderr.flush()
                    continue
            
            decrypted_row = row.copy()
            encrypted_value = row.get('value')
            decrypted_value = encryption.decrypt_value(encrypted_value)
            decrypted_row['value'] = decrypted_value
            decrypted_rows.append(decrypted_row)
        
        print(f"DEBUG: list_recent_sensor_data_by_location - Returning {len(decrypted_rows)} rows for location '{location}', user_id={user_id}", file=sys.stderr)
        sys.stderr.flush()
        return decrypted_rows
    except Exception as e:
        print(f"MySQL list_recent_sensor_data_by_location error: {e}")
        return []

def list_recent_water_readings(limit: int = 200):
    pool = get_pool()
    if pool is None:
        return []
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        cur.execute(
            """
            SELECT id, tds, ph, turbidity, created_at
            FROM water_readings
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            (int(limit),),
        )
        rows = cur.fetchall() or []
        cur.close()
        _return_connection(pool, conn)
        
        # Decrypt sensor values after retrieving from database
        encryption = get_db_encryption()
        decrypted_rows = []
        for row in rows:
            decrypted_row = row.copy()
            decrypted_row['tds'] = encryption.decrypt_value(row.get('tds'))
            decrypted_row['ph'] = encryption.decrypt_value(row.get('ph'))
            decrypted_row['turbidity'] = encryption.decrypt_value(row.get('turbidity'))
            decrypted_rows.append(decrypted_row)
        
        return decrypted_rows
    except Exception as e:
        print(f"MySQL list_recent_water_readings error: {e}")
        return []


# Device session management functions
def create_device_session(session_token: str, device_id: str, expires_at: datetime) -> bool:
    """Create a new device session in the database."""
    pool = get_pool()
    if pool is None:
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            INSERT INTO device_sessions (session_token, device_id, expires_at, counter)
            VALUES (%s, %s, %s, 0)
            """,
            (session_token, device_id, expires_at),
        )
        conn.commit()
        cur.close()
        _return_connection(pool, conn)
        return True
    except Error as e:
        # Duplicate session token (shouldn't happen with proper generation)
        if getattr(e, 'errno', None) == errorcode.ER_DUP_ENTRY:
            return False
        print(f"MySQL create_device_session error: {e}")
        return False


def get_device_session(session_token: str):
    """Get a device session by token."""
    pool = get_pool()
    if pool is None:
        return None
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn, dictionary=True)
        cur.execute(
            """
            SELECT session_token, device_id, counter, expires_at, created_at, last_used_at
            FROM device_sessions
            WHERE session_token = %s
            LIMIT 1
            """,
            (session_token,),
        )
        row = cur.fetchone()
        cur.close()
        _return_connection(pool, conn)
        return row
    except Exception as e:
        print(f"MySQL get_device_session error: {e}")
        return None


def update_device_session(session_token: str, counter: int, expires_at: datetime) -> bool:
    """Update device session counter and expiration."""
    pool = get_pool()
    if pool is None:
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            UPDATE device_sessions
            SET counter = %s, expires_at = %s, last_used_at = CURRENT_TIMESTAMP
            WHERE session_token = %s
            """,
            (counter, expires_at, session_token),
        )
        conn.commit()
        updated = cur.rowcount > 0
        cur.close()
        _return_connection(pool, conn)
        return updated
    except Exception as e:
        print(f"MySQL update_device_session error: {e}")
        return False


def delete_device_session(session_token: str) -> bool:
    """Delete a device session."""
    pool = get_pool()
    if pool is None:
        return False
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            DELETE FROM device_sessions WHERE session_token = %s
            """,
            (session_token,),
        )
        conn.commit()
        deleted = cur.rowcount > 0
        cur.close()
        _return_connection(pool, conn)
        return deleted
    except Exception as e:
        print(f"MySQL delete_device_session error: {e}")
        return False


def cleanup_expired_sessions() -> int:
    """Delete expired sessions. Returns number of deleted sessions."""
    pool = get_pool()
    if pool is None:
        return 0
    try:
        conn = _get_connection(pool)
        cur = _get_cursor(conn)
        cur.execute(
            """
            DELETE FROM device_sessions WHERE expires_at < NOW()
            """
        )
        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        _return_connection(pool, conn)
        return deleted_count
    except Exception as e:
        print(f"MySQL cleanup_expired_sessions error: {e}")
        return 0
import sqlite3

def check_subject_table_columns(database_file, table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    try:
        # Fetch table schema information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        if not columns:
            print(f"Table '{table_name}' does not exist in the database.")
            return

        # Retrieve primary key information from sqlite_master table
        cursor.execute(f"PRAGMA table_info({table_name})")
        primary_key_columns = [row[1] for row in cursor.fetchall() if row[5] == 1]

        print(f"Columns for table '{table_name}':")
        print("----------------------------")
        for column in columns:
            col_name = column[1]
            col_type = column[2]
            is_nullable = "YES" if column[3] == 1 else "NO"
            default_value = column[4] if column[4] else "None"

            # Check if column is part of the primary key
            is_primary_key = "Yes" if col_name in primary_key_columns else "No"

            print(f"Name: {col_name}")
            print(f"Type: {col_type}")
            print(f"Nullable: {is_nullable}")
            print(f"Default Value: {default_value}")
            print(f"Primary Key: {is_primary_key}")
            print("----------------------------")

    except sqlite3.Error as e:
        print(f"Error occurred: {e}")

    finally:
        # Close connection
        conn.close()

# Specify the database file path and table name
database_file_path = "db.sqlite3"
table_name = "attendance_attendance"

# Call the function to check the columns of the specified table
check_subject_table_columns(database_file_path, table_name)

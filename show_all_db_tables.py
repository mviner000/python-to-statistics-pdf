import sqlite3

def list_tables(db_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Query to retrieve the names of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    
    # Fetch all table names
    tables = cursor.fetchall()
    
    # Print each table name
    print("Tables in database:")
    for table in tables:
        print(table[0])
    
    # Close the database connection
    conn.close()

if __name__ == "__main__":
    db_file_path = 'db.sqlite3'  # Path to your SQLite database
    list_tables(db_file_path)

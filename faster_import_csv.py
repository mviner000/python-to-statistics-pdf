import csv
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='import_csv.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def import_attendance_data():
    success_count = 0
    error_count = 0
    batch_size = 1000  # Process 1000 records at a time
    
    # SQL insert statement
    insert_sql = '''
    INSERT INTO attendance_attendance 
    (id, school_id, full_name, time_in_date, classification, purpose)
    VALUES (?, ?, ?, ?, ?, ?)
    '''
    
    try:
        # Connect to SQLite database with optimized settings
        conn = sqlite3.connect('db.sqlite3', isolation_level='DEFERRED')
        conn.execute('PRAGMA journal_mode = WAL')  # Write-Ahead Logging for better concurrency
        conn.execute('PRAGMA synchronous = NORMAL')  # Faster disk write
        conn.execute('PRAGMA cache_size = -2000')  # Use 2MB cache
        conn.execute('PRAGMA temp_store = MEMORY')  # Store temp tables in memory
        
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')
        
        batch = []
        with open('attendance_3.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_number, row in enumerate(csv_reader, start=2):
                try:
                    # Parse time_in_date
                    time_in_date = datetime.fromisoformat(row['Time In Date'].replace('T', ' ').split('+')[0])
                    
                    # Prepare data tuple
                    data = (
                        row['ID'],
                        row['School ID'],
                        row['Full Name'],
                        time_in_date.isoformat(),
                        row['Classification'],
                        row['Purpose']
                    )
                    
                    batch.append(data)
                    
                    # Process batch when it reaches batch_size
                    if len(batch) >= batch_size:
                        cursor.executemany(insert_sql, batch)
                        success_count += len(batch)
                        batch = []
                        logging.info(f"Processed {success_count} records...")
                    
                except Exception as e:
                    error_count += 1
                    logging.error(f"Row {row_number}: Failed to process record for {row.get('Full Name', 'Unknown')}. Error: {str(e)}")
                    continue
        
        # Process remaining records
        if batch:
            cursor.executemany(insert_sql, batch)
            success_count += len(batch)
        
        # Commit transaction
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logging.critical(f"Critical error occurred: {str(e)}")
        return False
        
    finally:
        # Log summary
        logging.info(f"\nImport Summary:")
        logging.info(f"Total successful imports: {success_count}")
        logging.info(f"Total failed imports: {error_count}")
        
        print(f"Import completed. Check attendance_import.log for details.")
        print(f"Successful imports: {success_count}")
        print(f"Failed imports: {error_count}")
        
        # Close database connection
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    print("Starting import process...")
    import_attendance_data()
    print("Import process completed.")
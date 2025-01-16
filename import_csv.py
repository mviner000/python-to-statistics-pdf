import csv
import logging
import sqlite3
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    filename='import_csv.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def normalize_datetime_string(date_string):
    """
    Normalize the datetime string to handle extended precision microseconds
    """
    # Remove timezone if present
    if '+' in date_string:
        date_string = date_string.split('+')[0]
    
    # If there are microseconds (digits after decimal point)
    if '.' in date_string:
        # Split into main part and microseconds
        main_part, microseconds = date_string.split('.')
        # Take only first 6 digits of microseconds
        microseconds = microseconds[:6]
        # Recombine
        return f"{main_part}.{microseconds}"
    
    return date_string

def parse_datetime(date_string):
    """
    Parse datetime string after normalizing it
    """
    normalized_date = normalize_datetime_string(date_string)
    try:
        return datetime.strptime(normalized_date, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        try:
            return datetime.strptime(normalized_date, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            raise ValueError(f"Unable to parse date string: {date_string}")

def import_attendance_data():
    success_count = 0
    error_count = 0
    
    # SQL insert statement
    insert_sql = '''
    INSERT INTO attendance_attendance 
    (id, school_id, full_name, time_in_date, classification, purpose)
    VALUES (?, ?, ?, ?, ?, ?)
    '''
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('db4.sqlite3')
        cursor = conn.cursor()
        
        with open('attendance.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_number, row in enumerate(csv_reader, start=2):  # Start from 2 to account for header
                try:
                    # Parse the datetime
                    time_in_date = parse_datetime(row['Time In Date'])
                    
                    # Format for SQLite (standard format with 6-digit microseconds)
                    formatted_date = time_in_date.strftime('%Y-%m-%d %H:%M:%S.%f')
                    
                    # Prepare data tuple for insertion
                    data = (
                        row['ID'],
                        row['School ID'],
                        row['Full Name'],
                        formatted_date,
                        row['Classification'],
                        row['Purpose']
                    )
                    
                    # Execute insert
                    cursor.execute(insert_sql, data)
                    conn.commit()
                    
                    success_count += 1
                    logging.info(f"Row {row_number}: Successfully imported attendance record for {row['Full Name']}")
                    
                except Exception as e:
                    error_count += 1
                    logging.error(f"Row {row_number}: Failed to import attendance record for {row.get('Full Name', 'Unknown')}.")
                    logging.error(f"Raw date value: {row.get('Time In Date', 'No date found')}")
                    logging.error(f"Error details: {str(e)}")
                    conn.rollback()
                    continue
                
    except Exception as e:
        logging.critical(f"Critical error occurred while processing the CSV file: {str(e)}")
        return False
        
    finally:
        # Log summary
        logging.info(f"\nImport Summary:")
        logging.info(f"Total successful imports: {success_count}")
        logging.info(f"Total failed imports: {error_count}")
        
        print(f"Import completed. Check import_csv.log for details.")
        print(f"Successful imports: {success_count}")
        print(f"Failed imports: {error_count}")
        
        # Close database connection
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    import_attendance_data()
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

def parse_datetime(date_str, time_str):
    """
    Parse and combine date and time strings into a datetime object
    """
    try:
        # Parse date (assuming MM/DD/YYYY format)
        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
        
        # Parse time (12-hour format with AM/PM)
        time_obj = datetime.strptime(time_str, '%I:%M %p')
        
        # Combine date and time
        combined_datetime = datetime.combine(
            date_obj.date(),
            time_obj.time()
        )
        
        return combined_datetime
    except ValueError as e:
        raise ValueError(f"Error parsing date/time: {date_str} {time_str}. Error: {str(e)}")

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
        conn = sqlite3.connect('db5.sqlite3')
        cursor = conn.cursor()
        
        with open('attendance_1-13.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_number, row in enumerate(csv_reader, start=2):  # Start from 2 to account for header
                try:
                    # Combine and parse the date and time
                    time_in_date = parse_datetime(row['Date'], row['Time'])
                    
                    # Format for SQLite
                    formatted_date = time_in_date.strftime('%Y-%m-%d %H:%M:%S')
                    
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
                    logging.error(f"Raw date: {row.get('Date', 'No date')} time: {row.get('Time', 'No time')}")
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
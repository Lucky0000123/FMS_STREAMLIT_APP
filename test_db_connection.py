import os
import pyodbc
import time

def test_connection():
    # Print environment variables for debugging
    print("Environment variables:")
    print(f"SQL_SERVER: {os.environ.get('SQL_SERVER', 'Not set')}")
    print(f"SQL_DATABASE: {os.environ.get('SQL_DATABASE', 'Not set')}")
    print(f"SQL_USERNAME: {os.environ.get('SQL_USERNAME', 'Not set')}")
    print(f"SQL_PASSWORD: {'*****' if os.environ.get('SQL_PASSWORD') else 'Not set'}")
    
    # List available ODBC drivers
    print("\nAvailable ODBC drivers:")
    print(pyodbc.drivers())
    
    # Construct connection string based on environment variables
    if os.environ.get('SQL_USERNAME') and os.environ.get('SQL_PASSWORD'):
        # SQL Authentication
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ.get('SQL_SERVER', '10.211.10.2')};"
            f"DATABASE={os.environ.get('SQL_DATABASE', 'FMS_Safety')};"
            f"UID={os.environ.get('SQL_USERNAME')};"
            f"PWD={os.environ.get('SQL_PASSWORD')};"
            f"TrustServerCertificate=yes;"
        )
        print("\nUsing SQL Authentication")
    else:
        # Windows Authentication
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ.get('SQL_SERVER', 'DESKTOP-JQDJV8F')};"
            f"DATABASE={os.environ.get('SQL_DATABASE', 'FMS_Safety')};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        print("\nUsing Windows Authentication")
    
    # Print connection string (with password masked)
    masked_conn_str = conn_str
    if os.environ.get('SQL_PASSWORD'):
        masked_conn_str = masked_conn_str.replace(os.environ.get('SQL_PASSWORD'), '*****')
    print(f"Connection string: {masked_conn_str}")
    
    # Try to connect
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\nAttempt {attempt}/{max_retries} to connect to SQL Server...")
            conn = pyodbc.connect(conn_str, timeout=10)
            cursor = conn.cursor()
            
            # Test query
            print("Connection successful! Executing test query...")
            cursor.execute("SELECT @@VERSION")
            row = cursor.fetchone()
            print(f"SQL Server version: {row[0]}")
            
            # Close connection
            cursor.close()
            conn.close()
            print("Database connection test completed successfully.")
            return True
        
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not connect to the database.")
                return False

if __name__ == "__main__":
    test_connection()

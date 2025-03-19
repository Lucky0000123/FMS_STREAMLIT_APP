import pyodbc
import pandas as pd

# SQL Server connection details
server = '10.211.10.2'
database = 'FMS_DB'
username = 'headofnickel'
password = 'Dataisbeautifulrev001!'

# Connect to SQL Server
conn = pyodbc.connect(
    f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
)

# Define your query (Replace 'your_table' with your actual table)
query = "SELECT * FROM your_table"

# Fetch data
df = pd.read_sql(query, conn)

# Save it as CSV (Optional if uploading to Snowflake)
df.to_csv("data.csv", index=False)

# Close the connection
conn.close()

print("Data fetched successfully!")

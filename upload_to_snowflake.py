import snowflake.connector
import pandas as pd

# Snowflake connection details
sf_conn = snowflake.connector.connect(
    user='your_snowflake_user',
    password='your_snowflake_password',
    account='your_snowflake_account'
)

cur = sf_conn.cursor()

# Create Table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS FMS_DB.PUBLIC.your_table (
    column1 STRING,
    column2 STRING,
    column3 INT
);
""")

# Load CSV into DataFrame
df = pd.read_csv("data.csv")

# Insert Data into Snowflake
for _, row in df.iterrows():
    cur.execute(f"""
    INSERT INTO FMS_DB.PUBLIC.your_table (column1, column2, column3)
    VALUES ('{row[0]}', '{row[1]}', {row[2]});
    """)

sf_conn.commit()
cur.close()
sf_conn.close()

print("✅ Data uploaded to Snowflake successfully!")

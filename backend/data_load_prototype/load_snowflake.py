
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

def load_csv_to_snowflake(
    csv_path,
    table_name,
    snowflake_config
):
    # Load the cleaned DataFrame
    df = pd.read_csv(csv_path)

    # Connect to Snowflake
    conn = snowflake.connector.connect(
        user=snowflake_config["user"],
        password=snowflake_config["password"],
        account=snowflake_config["account"],
        warehouse=snowflake_config["warehouse"],
        database=snowflake_config["database"],
        schema=snowflake_config["schema"]
    )
    cursor = conn.cursor()

    # Ensure table exists (optional: create dynamically)
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        Question TEXT,
        Answer TEXT,
        Category TEXT,
        Difficulty TEXT
    );
    """)

    # Upload DataFrame to Snowflake
    success, nchunks, nrows, _ = write_pandas(conn, df, table_name)
    
    print(f" Upload successful: {success} | Rows uploaded: {nrows}")

    cursor.close()
    conn.close()

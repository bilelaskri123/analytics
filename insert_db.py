from sqlalchemy import create_engine, Integer, text
from dotenv import load_dotenv
import urllib.parse
import os

load_dotenv()  # Load environment variables from .env file
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", '3306')  # Default to 3306 if not set
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD", "")
safe_password = urllib.parse.quote_plus(db_password)
print(f"Connecting to DB at {db_host}:{db_port} with user '{db_user}' and password: {safe_password}")


def insertInDB(df):
    try:
        connection_string = f"mysql+pymysql://{db_user}:{safe_password}@{db_host}:{db_port}/{db_name}"
        print(f"Connecting to database with: {connection_string}")
        engine = create_engine(connection_string)
        # Set DataFrame index to start at 1 and name it 'id' so it's written as a column
        df.index = df.index + 1
        df.index.name = 'id'
        # Write the index as a column (index=True) so 'id' is created in the table
        df.to_sql("list_versement", con=engine, if_exists="replace", index=True, dtype={"id": Integer})
        # Ensure the id column is AUTO_INCREMENT and primary key
        alter_sql = text("ALTER TABLE list_versement MODIFY COLUMN id INT AUTO_INCREMENT PRIMARY KEY;")
        with engine.begin() as connection:
            connection.execute(alter_sql)
            

        print("Success! The table has been created. 'id' starts at 1, is Unique, and is Auto-Incrementing.")
        print("✅ Data inserted into database successfully.")
    except Exception as e:
        print(f"❌ Database insertion error: {e}")
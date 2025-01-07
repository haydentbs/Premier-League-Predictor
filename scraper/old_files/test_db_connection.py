import os
import time
from sqlalchemy import create_engine, text
import psycopg2

def test_sqlalchemy_connection():
    print("\nTesting SQLAlchemy connection...")
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'db'),
        'database': os.getenv('POSTGRES_DB', 'premier_league'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    print(f"Connection details (password hidden):")
    debug_config = dict(db_config)
    debug_config['password'] = '****'
    print(debug_config)
    
    try:
        engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"Successfully connected to PostgreSQL!")
            print(f"Database version: {version}")
            
        return True
    except Exception as e:
        print(f"SQLAlchemy connection failed: {str(e)}")
        return False

def test_psycopg2_connection():
    print("\nTesting psycopg2 connection...")
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'db'),
            database=os.getenv('POSTGRES_DB', 'premier_league'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"Successfully connected to PostgreSQL!")
        print(f"Database version: {version[0]}")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"psycopg2 connection failed: {str(e)}")
        return False

def main():
    print("Starting database connection tests...")
    print(f"Current environment variables:")
    print(f"POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'db')}")
    print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT', '5432')}")
    print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB', 'premier_league')}")
    print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER', 'postgres')}")
    
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        print(f"\nAttempt {attempt + 1} of {max_retries}")
        
        sqlalchemy_success = test_sqlalchemy_connection()
        psycopg2_success = test_psycopg2_connection()
        
        if sqlalchemy_success and psycopg2_success:
            print("\nAll connection tests passed!")
            return True
            
        if attempt < max_retries - 1:
            print(f"\nRetrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print("\nFailed to establish database connections after all attempts")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
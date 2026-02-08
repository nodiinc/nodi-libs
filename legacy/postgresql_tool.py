import psycopg2
import psycopg2.extras

class PostgreSqlClient:
    """PostgreSQL Client"""

    def __init__(self, host, port, username, password, db):
        self.connection_string = (f'host={host} '
                                  f'port={port} '
                                  f'user={username} '
                                  f'password={password} '
                                  f'dbname={db}')

    def connect(self, autocommit=False):
        """Connect DB"""
        self.connection = psycopg2.connect(self.connection_string)
        self.cursor = self.connection.cursor()
        self.connection.autocommit = autocommit

    def disconnect(self):
        """Disconnect DB"""
        self.connection.close()

    def execute_one(self, query, value=None):
        """Execute one SQL"""
        if value:
            self.cursor.execute(query, tuple(value))
        else:
            self.cursor.execute(query)

    def execute_many(self, query, values):
        """Execute many SQLs"""
        self.cursor.executemany(query, values)

    def execute_batch(self, query, values):
        """Execute many SQLs in batch"""
        psycopg2.extras.execute_batch(self.cursor, query, values)
    
    def execute_values(self, query, values, template=None):
        """Execute many SQLs in list"""
        psycopg2.extras.execute_values(self.cursor, query, values, template)
    
    def fetch_one(self, query):
        """Execute SQL and fetch one result"""
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return list(result)

    def fetch_many(self, query, size):
        """Execute SQL and fetch many results"""
        self.cursor.execute(query)
        result = self.cursor.fetchmany(size)
        return [list(i) for i in result]

    def fetch_all(self, query):
        """Execute SQL and fetch all results"""
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        return [list(item) for item in result]

    def commit(self):
        """Manual commit"""
        self.connection.commit()

    def rollback(self):
        """Manual rollback"""
        self.connection.rollback()
    
    def execute_one_auto(self, query, value=None):
        """Automatic package to execute one SQL"""
        self.connect()
        result = self.execute_one(query, value)
        self.commit()
        self.disconnect()
        return result
    
    def execute_many_auto(self, query, values):
        """Automatic package to execute many SQLs"""
        self.connect()
        result = self.execute_values(query, values)
        self.commit()
        self.disconnect()
        return result
    
    def fetch_one_auto(self, query):
        """Automatic package to execute SQL and fetch one result"""
        self.connect()
        result = self.fetch_one(query)
        self.disconnect()
        return result
    
    def fetch_many_auto(self, query, size):
        """Automatic package to execute SQL and fetch many results"""
        self.connect()
        result = self.fetch_many(query, size)
        self.disconnect()
        return result
    
    def fetch_all_auto(self, query):
        """Automatic package to execute SQL and fetch all results"""
        self.connect()
        result = self.fetch_all(query)
        self.disconnect()
        return result

if __name__ == "__main__":

    import logging
    import time

    try:
        pg1 = PostgreSqlClient("localhost", "5432", "postgres", "aa001234", "postgres")
        pg1.connect()
        sql = """SELECT *
            FROM pg_tables
            WHERE schemaname = 'public';"""
        sql = """SELECT COUNT(*) FROM test_table;"""
        print(pg1.fetch_many(sql, 1))

        pg1.disconnect()
    except Exception as e:
        logging.error(e)
        print(e)

"""
execute_many

    * query: str
        INSERT INTO table (column1, column2, ...)
        VALUES %s

    * values: list of tuple
        [(value1, value2, ...), (value3, value4, ...), ...]

    * How it works: Execute insert operations repeatedly
        execute: INSERT INTO test_table (a, b, c) VALUES (1, 2, 3);
        execute: INSERT INTO test_table (a, b, c) VALUES (10, 20, 30);
        execute: INSERT INTO test_table (a, b, c) VALUES (100, 200, 300);

execute_batch

    * query: str
        INSERT INTO table (column1, column2, ...)
        VALUES %s

    * values: list of tuple
        [(value1, value2, ...), (value3, value4, ...), ...]

    * How it works: Execute insert operations in batch
        execute: INSERT INTO test_table (a, b, c) VALUES (1, 2, 3);
                 INSERT INTO test_table (a, b, c) VALUES (10, 20, 30);
                 INSERT INTO test_table (a, b, c) VALUES (100, 200, 300);

execute_values

    * query: str
        INSERT INTO table (column1, column2, ...)
        VALUES %s

    * values: list of tuple
        [(value1, value2, ...), (value3, value4, ...), ...]

    * How it works: Execute insert operation with zipped values list
        execute: INSERT INTO test_table (a, b, c)
                 VALUES [(1, 2, 3), (10, 20, 30), (100, 200, 300)];
"""
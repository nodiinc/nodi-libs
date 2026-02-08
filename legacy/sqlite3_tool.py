import sqlite3

class Sqlite3Client:
    """Sqlite3 Client"""
    
    def __init__(self, path):
        self.path = path

    def connect(self, autocommit=False):
        """Connect DB"""
        self.connection = sqlite3.connect(self.path)
        if autocommit:
            self.connection.isolation_level = None
        self.cursor = self.connection.cursor()

    def disconnect(self):
        """Disconnect DB"""
        self.connection.close()

    def execute_one(self, query, value=None):
        """Execute one SQL"""
        if value:
            result = self.cursor.execute(query, value)
        else:
            result = self.cursor.execute(query)
        return result

    def execute_many(self, query, values):
        """Execute many SQLs"""
        result = self.cursor.executemany(query, values)
        return result

    def fetch_one(self, query):
        """Execute SQL and fetch one result"""
        result = self.cursor.execute(query).fetchone()
        return list(result) if result else result

    def fetch_many(self, query, size):
        """Execute SQL and fetch many results"""
        result = self.cursor.execute(query).fetchmany(size)
        return [list(i) for i in result]

    def fetch_all(self, query):
        """Execute SQL and fetch all results"""
        result = self.cursor.execute(query).fetchall()
        return [list(i) for i in result]

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
        result = self.execute_many(query, values)
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
    sqc = Sqlite3Client('/root/test/test.db')
    sqc.connect()
    data = [[2,3,4,5,6],
            [3,4,5,6,7]]
    sqc.execute_many('INSERT INTO test_table VALUES (?,?,?,?,?)', data)
    sqc.commit()
    read = sqc.fetch_all('SELECT * FROM test_table')
    print(read)
    
"""
.help
.table
.schema
.exit
.header on
.mode column
PRAMGA foreign_keys = 1;
"""
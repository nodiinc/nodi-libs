import pymssql

class MssqlClient:
    """PostgreSQL 클라이언트"""

    def __init__(self, host, port, username, password, db):
        self.server = f'{host}:{port}'
        self.db = db
        self.username = username
        self.password = password

    def connect(self, autocommit=False):
        """DB 연결"""
        self.connection = pymssql.connect(server   = self.server,
                                   user     = self.username,
                                   password = self.password,
                                   database = self.db,
                                   autocommit = autocommit)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        """DB 해제"""
        self.connection.close()

    def execute_one(self, sql, value=None):
        """SQL 한 건 실행"""
        if value:
            self.cursor.execute(sql, tuple(value))
        else:
            self.cursor.execute(sql)
        
        """
            sql: str
                INSERT INTO tbl_nm (col1_nm, col2_nm, ...)
                VALUES (%s, %s, ...)
                
            var: tuple
                (vl1, vl2, ...)
        """

    def execute_many(self, sql, value_list):
        """SQL 여러 건 for문으로 실행"""
        self.cursor.executemany(sql, [tuple(i) for i in value_list])
        """
            sql: str
                INSERT INTO tbl_nm (col1_nm, col2_nm, ...)
                VALUES (%s, %s, ...)
                
            var_ls: list of tuple
                [(vl1, vl2, ...), (vl1, vl2, ...), ...]
                
            principle
                execute insert operations repeatedly
        """
    
    def fetch_one(self, sql):
        """SQL 실행 후 결과 한 건 가져오기"""
        self.cursor.execute(sql)
        return list(self.cursor.fetchone())

    def fetch_many(self, sql, size):
        """SQL 실행 후 결과 여러 건 가져오기"""
        self.cursor.execute(sql)
        return [list(i) for i in self.cursor.fetchmany(size)]

    def fetch_all(self, sql):
        """SQL 실행 후 결과 모두 가져오기"""
        self.cursor.execute(sql)
        return [list(item) for item in self.cursor.fetchall()]

    def commit(self):
        """수동 커밋"""
        self.connection.commit()

    def rollback(self):
        """수동 롤백"""
        self.connection.rollback()


if __name__ == '__main__':

    msc = MssqlClient('59.24.59.182', '49100', 'ingent_sa', 'dlswl(!0O', 'EnterbuilderI')
    msc.connect()
    
    # sql = """DELETE FROM proc_data_rt"""
    # print(msc.execute_one(sql))
    
    # sql = """INSERT INTO proc_data_rt
    #     VALUES (%s, %s, %s, %s, %s)"""
    # vl = [['test1', '2023-11-14 00:00:00', 'good', '777', None],
    #     ['test2', '2023-11-14 00:00:00', 'good', '777', None],
    #     ['test3', '2023-11-14 00:00:00', 'good', '777', None]]
    # print(msc.execute_many(sql, vl))
    # print(msc.commit())

    sql = """UPDATE proc_data_rt
             SET tag_tm = %s, tag_data = %s, tag_status = %s, tag_cmnt = %s WHERE tag_no = %s"""
    vl = [['2023-11-14 12:00:00', 'good', '888', None, 'test1'],
          ['2023-11-14 12:00:00', 'good', '888', None, 'test2'],
          ['2023-11-14 12:00:00', 'good', '888', None, 'test3']]
    print(msc.execute_many(sql, vl))
    print(msc.commit())

    sql = """SELECT * FROM proc_data_rt"""
    print(msc.fetch_all(sql))

    msc.disconnect()
    
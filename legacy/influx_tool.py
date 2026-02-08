from influxdb import InfluxDBClient as _InfluxDBClient

class InfluxDbClient:
    """InfluxDB Client"""
    # db = sum(meas)
    # meas = sum(pnt)
    # pnt = tag + field + ts
    # ser = meas + tag

    def __init__(self, host='localhost', port=8086,
                 username='root', password='root', db=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db = db
    
    def connect(self):
        """Connect DB"""
        # cmd: USE {db}
        self.client = _InfluxDBClient(host=self.host,
                                      port=self.port,
                                      username=self.username,
                                      password=self.password,
                                      database=self.db)

    def disconnect(self):
        """Disconnect DB"""
        self.client.close()

    def create_user(self, username, password, admin=False):
        """Create user"""
        self.client.create_user(username, password, admin)

    def drop_user(self, username):
        """Drop user"""
        self.client.drop_user(username)

    def read_user(self):
        """Read user list"""
        result = self.client.get_list_users()
        return result

    def create_db(self, db):
        """Create DB"""
        self.client.create_database(db)

    def drop_db(self, db):
        """Drop DB"""
        self.client.drop_database(db)
        
    def read_db(self):
        """Read DB list"""
        # cmd: SHOW DATABASES
        result = self.client.get_list_database()
        return result

    def create_retpol(self, name, db=None, duration='1d',
                      shard_duration='0s', replication=1, default=False):
        """Create retention policy"""
        # qry: CREATE RETENTION POLICY {policy}
        #      ON {database}
        #      DURATION {duration}
        #      SHARD DURATION {shard_duration}
        #      REPLICATION {replication}
        #      [DEFAULT]
        self.client.create_retention_policy(name=name,
                                            duration=duration,
                                            replication=replication,
                                            database=db,
                                            default=default,
                                            shard_duration=shard_duration)

    def alter_retpol(self, name, db=None, duration='1d',
                     shard_duration='0s', replication=1, default=False):
        """Alter retention policy"""
        # qry: ALTER RETENTION POLICY {policy}
        #      ON {database}
        #      DURATION {duration}
        #      SHARD DURATION {shard_duration}
        #      REPLICATION {replication}
        #      [DEFAULT]
        self.client.alter_retention_policy(name=name,
                                           database=db,
                                           duration=duration,
                                           replication=replication,
                                           default=default,
                                           shard_duration=shard_duration)

    def drop_retpol(self, name, db=None):
        """Drop retention policy"""
        # qry: DROP RETENTION POLICY {policy}
        #      ON {database}
        self.client.drop_retention_policy(name=name, database=db)

    def read_retpol(self, db=None):
        """Read retention policy list"""
        # ry: SHOW RETENTION POLICIES
        #     ON {database}
        result = self.client.get_list_retention_policies(database=db)
        return result

    def drop_meas(self, measurement):
        """Drop measurement"""
        self.client.drop_measurement(measurement)

    def read_meas(self):
        """Read measurement list"""
        result = self.client.get_list_measurements()
        return result

    def execute_one(self, query, db=None):
        """Execute SQL"""
        # qry: INSERT {series} {field} [timestamp]
        #      = INSERT {meas},{tag} {field} [timestamp]
        #      = INSERT {meas},{tag1_nm}={tag1_vl},{tag2_nm}={tag2_vl},...
        #               {field1_nm}={field1_vl},{field2_nm}={field2_vl},... [ts]
        result = self.client.query(query=query,
                                   database=db)
        return result

    def fetch_all(self, query, db=None):
        """Execute SQL and fetch all results"""
        result = self.client.query(query=query,
                                   database=db)
        points = list(result.get_points())
        return points
    
    def read_series(self, db=None, measurement=None, tag=None):
        """Read series list"""
        result = self.client.get_list_series(database=db,
                                             measurement=measurement,
                                             tags=tag)
        return result
    
    def write_points(self, point_list, time_unit='s', db=None,
                     retpol=None, batch_size=None):
        """Write points"""
        # points = [
        #     {
        #         'measurement': 'elec_meas',
        #         'tags': {'loc': 'beom', 'fac': 'chem'},
        #         'fields': {'v': 123, 'i': 456},
        #         'time': datetime.datetime(2022, 11, 30, 22, 50, 55, 856062)
        #     },
        #     ...
        # ]
        result = self.client.write_points(points=point_list,
                                          time_precision=time_unit,
                                          database=db,
                                          retention_policy=retpol,
                                          batch_size=batch_size)
        return result

if __name__ == '__main__':
    influx = InfluxDbClient(db='nodi')
    influx.connect()
    l = influx.fetch_all('SELECT * FROM "arcv1"', 'nodi')
    from pprint import pprint
    for d in l:
        print(list(d.values()))
 
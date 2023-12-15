import mysql.connector
from mysql.connector import errorcode
import urllib.parse


class MySQLDatabase:
    def __init__(self):
        self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def connect_with_url(self, url):
        try:
            parsed_url = urllib.parse.urlparse(url)
            username = parsed_url.username
            password = parsed_url.password
            host = parsed_url.hostname
            port = parsed_url.port or 3306
            database = parsed_url.path[1:]  # Removing the leading '/'

            self.conn = mysql.connector.connect(
                user=username,
                password=password,
                host=host,
                port=port,
                database=database,
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
            self.conn = None

    def upsert(self, table_name, _dict):
        cursor = self.conn.cursor()
        placeholders = ", ".join(["%s"] * len(_dict))
        columns = ", ".join(_dict.keys())
        sql = (
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE "
            + ", ".join([f"{key} = VALUES({key})" for key in _dict.keys()])
        )
        cursor.execute(sql, list(_dict.values()))
        self.conn.commit()
        cursor.close()

    def delete(self, table_name, _id):
        cursor = self.conn.cursor()
        sql = f"DELETE FROM {table_name} WHERE id = %s"
        cursor.execute(sql, (_id,))
        self.conn.commit()
        cursor.close()

    def get(self, table_name, _id):
        cursor = self.conn.cursor()
        sql = f"SELECT * FROM {table_name} WHERE id = %s"
        cursor.execute(sql, (_id,))
        result = cursor.fetchone()
        cursor.close()
        return result

    def get_all(self, table_name):
        if self.conn is None:
            print("No database connection.")
            return None
        cursor = self.conn.cursor()
        sql = f"SELECT * FROM {table_name}"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def run_sql(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def get_table_definitions(self, table_name):
        return self.run_sql(f"SHOW CREATE TABLE {table_name}")[0][1]

    def get_all_table_names(self):
        return [x[0] for x in self.run_sql("SHOW TABLES")]

    def get_table_definitions_for_prompt(self):
        tables = self.get_all_table_names()
        return "\n\n".join([self.get_table_definitions(table) for table in tables])

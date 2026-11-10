import os
import re
import sqlite3

try:
    import pymysql.cursors
except ImportError:  # pragma: no cover
    pymysql = None


class MySQLConnection:
    def __init__(self, db):
        if pymysql is None:
            raise ImportError("pymysql is not installed")
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='root',
            db=db,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        self.connection = connection

    def query_db(self, query, data=None):
        with self.connection.cursor() as cursor:
            try:
                query_to_run = cursor.mogrify(query, data)
                print("Running Query:", query_to_run)
                cursor.execute(query_to_run, data or ())
                if query.lower().find("insert") >= 0:
                    self.connection.commit()
                    return cursor.lastrowid
                elif query.lower().find("select") >= 0:
                    return cursor.fetchall()
                else:
                    self.connection.commit()
            except Exception as e:
                print("Something went wrong", e)
                return False
            finally:
                self.connection.close()


class SQLiteConnection:
    def __init__(self, db):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f"{db}.sqlite3")
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def query_db(self, query, data=None):
        try:
            sqlite_query = query
            params = data or ()

            if data is not None:
                sqlite_query = re.sub(r"%\((\w+)\)s", r":\1", sqlite_query)
                sqlite_query = sqlite_query.replace("NOW()", "CURRENT_TIMESTAMP")
            else:
                sqlite_query = sqlite_query.replace("NOW()", "CURRENT_TIMESTAMP")

            print("Running Query:", sqlite_query, params)
            cursor = self.connection.execute(sqlite_query, params)

            if "insert" in sqlite_query.lower():
                self.connection.commit()
                return cursor.lastrowid
            elif "select" in sqlite_query.lower():
                return [dict(row) for row in cursor.fetchall()]
            else:
                self.connection.commit()
        except Exception as e:
            print("Something went wrong", e)
            return False


def connectToMySQL(db):
    candidate_names = [db, "CRusuario", "esquema_usuario"]
    unique_candidates = []
    for name in candidate_names:
        if name not in unique_candidates:
            unique_candidates.append(name)

    for candidate in unique_candidates:
        try:
            return MySQLConnection(candidate)
        except Exception:
            continue

    return SQLiteConnection(db)
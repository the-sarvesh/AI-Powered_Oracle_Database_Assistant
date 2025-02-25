import cx_Oracle
from typing import Optional, List, Dict
import pandas as pd

class OracleManager:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.conn = None

    def connect(self, username: str, password: str) -> bool:
        """Establish connection to Oracle database."""
        try:
            # Parse DSN components
            host, port_service = self.dsn.split(":", 1)
            port, service_name = port_service.split("/", 1)

            self.conn = cx_Oracle.connect(
                user=username,
                password=password,
                dsn=cx_Oracle.makedsn(
                    host,
                    int(port),
                    service_name=service_name
                )
            )
            print("Connection successful.")
            return True

        except cx_Oracle.DatabaseError as e:
            error = e.args[0]
            print(f"Oracle Connection Error: ORA-{error.code}: {error.message}")
            return False
        except ValueError as e:
            print(f"Invalid DSN format: {self.dsn}. Use 'host:port/service_name'.")
            return False
        except Exception as e:
            print(f"General Connection Error: {str(e)}")
            return False

    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as a DataFrame.
        Raises exceptions for errors to be handled by the application.
        """
        try:
            if not self.conn:
                raise Exception("No active connection to the database.")

            # Strip trailing semicolon
            sql = sql.rstrip(";")

            with self.conn.cursor() as cursor:
                cursor.execute(sql)

                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    return pd.DataFrame(cursor.fetchall(), columns=columns)

                # Return empty DataFrame if no rows are returned
                return pd.DataFrame()

        except cx_Oracle.DatabaseError as e:
            error = e.args[0]
            raise Exception(f"Oracle Execution Error: ORA-{error.code}: {error.message}")
        except Exception as e:
            raise Exception(f"General Execution Error: {str(e)}")


    def get_performance_data(self) -> List[Dict]:
        """Retrieve slow-performing queries from V$SQL."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT sql_id, sql_text, elapsed_time, executions
                    FROM V$SQL 
                    WHERE elapsed_time > 1000000
                    ORDER BY elapsed_time DESC
                """)
                return [
                    dict(zip(
                        ["sql_id", "sql_text", "elapsed_time", "executions"],
                        row
                    ))
                    for row in cursor.fetchall()
                ]
        except cx_Oracle.DatabaseError as e:
            error = e.args[0]
            print(f"Performance Data Error: ORA-{error.code}: {error.message}")
            return []
        

    def get_table_metadata(self, sql: str) -> Optional[pd.DataFrame]:
        """
        Fetch and return metadata of the table involved in the SQL query.
        """
        try:
            # Extract table name from the SQL query (basic implementation)
            table_name = sql.split("FROM")[1].split()[0]

            # Query to fetch metadata
            metadata_query = f"""
                SELECT column_name, data_type, data_length
                FROM all_tab_columns
                WHERE table_name = UPPER('{table_name}')
            """

            with self.conn.cursor() as cursor:
                cursor.execute(metadata_query)
                columns = [col[0] for col in cursor.description]
                return pd.DataFrame(cursor.fetchall(), columns=columns)

        except Exception as e:
            print(f"Error fetching metadata: {str(e)}")
            return None


    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

import pandas as pd


class CargoReader:
    """
    Connection to CargoWise One Microsoft SQL
    Server Database used for reading objects.

    Args:
        server_name (str):   Server Name.
        username (str):      Username.
        password (str):      Password.
        database_name (str): Database Name.
    """   

    def __init__(
        self,
        server_name    : str,
        username      : str,
        password      : str,
        database_name : str
    ):
        """
        Establish a connection with the
        Microsoft SQL Server Database.

        Args:
            server_name (str):   Server Name.
            username (str):      Username.
            password (str):      Password.
            database_name (str): Database Name.
        """        
        
        import sqlalchemy
        from sqlalchemy.engine import URL

        url = URL.create(
            drivername="mssql+pyodbc",
            username=username,
            password=password,
            host=server_name,
            database=database_name,
            query={
                "driver" : "ODBC Driver 18 for SQL Server",
                "Encrypt" : "yes",
                "TrustServerCertificate" : "yes"
            }
        )

        engine = sqlalchemy.create_engine(url)

        self.connection = engine.connect()
    

    def query(
        self,
        query : str
    ) -> pd.DataFrame:
        """
        Execute a SQL query on the database
        and return the result as a DataFrame.

        Args:
            query (str): The SQL query.

        Returns:
            pd.DataFrame: The query result.
        """
        return pd.read_sql(query, self.connection)


if __name__ == "__main__":

    import os

    import pandas as pd
    from dotenv import load_dotenv

    load_dotenv()

    class MissingConfiguration(Exception): pass

    use_prod : bool = True
    name = "PROD" if use_prod else "TEST"
    
    connection_variables = [
        f"CW_DB_{name}_SERVER",
        f"CW_DB_{name}_USER",
        f"CW_DB_{name}_PASSWORD",
        f"CW_DB_{name}_DATABASE"
    ]

    try:
        SERVER, USER, PASS, DBNAME = [os.environ[i] for i in connection_variables]
    except KeyError:
        raise MissingConfiguration(
            "Missing environment variables: "
            f"{[i for i in connection_variables if os.getenv(i) is None]}"
        )

    conn = CargoReader(
        SERVER, USER, PASS, DBNAME
    )

    query = """
SELECT TOP 10 * FROM dbo.StorageDocs WHERE
SC_DocType = 'POD' ORDER BY SC_Date DESC;
    """

    result = conn.query(query)

    print(result)
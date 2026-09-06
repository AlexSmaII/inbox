import pandas as pd

from cwio import credentials


class CargoReader:
    """
    Connection to CargoWise One Microsoft SQL
    Server database used for reading objects.
    Uses credentials from .env by default unless
    they are given as arguments.

    Args:
        production (bool, optional):
            Use CW1 production database rather than test database.
            Only has any effect if using default connection values.
        server_name (str, optional):   Server Name.
        username (str, optional):      Username.
        password (str, optional):      Password.
        database_name (str, optional): Database Name.
    """   
    
    def __init__(
        self,
        production : bool = False,
        server_name   : str | None = None,
        username      : str | None = None,
        password      : str | None = None,
        database_name : str | None = None
    ):
        """
        Create a new CargoWise SQL Server connection.
        Uses credentials from .env by default unless
        they are given as class constructor arguments.

        Args:
            production (bool, optional):
                Use CW1 production database rather than test database.
                Only has any effect if using default connection values.
            server_name (str, optional):   Server Name.
            username (str, optional):      Username.
            password (str, optional):      Password.
            database_name (str, optional): Database Name.
        """
        
        if not any([
            server_name,
            username,
            password,
            database_name
        ]):
            server_name, username, password, database_name = credentials.read(
                production=production
            )

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

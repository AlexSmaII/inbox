def generate_connection_string(
    server_url : str,
    username : str,
    password : str,
    database_name : str,
    driver : str = "ODBC Driver 18 for SQL Server"
) -> str:

    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server_url}",
        "Encrypt=yes",
        "TrustServerCertificate=yes",
    ]
    if database_name:
        parts.insert(2, f"DATABASE={database_name}")

    # parts.append("Trusted_Connection=yes")
    parts.append(f"UID={username}")
    parts.append(f"PWD={password}")

    return ";".join(parts) + ";"


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

    import sqlalchemy
    from sqlalchemy.engine import URL

    url = URL.create(
        drivername="mssql+pyodbc",
        username=USER,
        password=PASS,
        host=SERVER,
        database=DBNAME,
        query={
            "driver" : "ODBC Driver 18 for SQL Server",
            "Encrypt" : "yes",
            "TrustServerCertificate" : "yes"
        }
    )

    engine = sqlalchemy.create_engine(url)

    conn = engine.connect()

    query = """
SELECT TOP 10 * FROM dbo.StorageDocs WHERE
SC_DocType = 'POD' ORDER BY SC_Date DESC;
    """

    result = pd.read_sql(query, conn)

    print(result)
def generate_connection_string(
    server_url : str,
    username : str,
    password : str,
    driver : str = "ODBC Driver 18 for SQL Server",
    database_name : str | None = None
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

    from dotenv import load_dotenv

    load_dotenv()

    class MissingConfiguration(Exception): pass

    try:
        USER   = os.environ["CW_DB_TEST_USER"]
        PASS   = os.environ["CW_DB_TEST_PASSWORD"]
        SERVER = os.environ["CW_DB_TEST_SERVER"]
    except KeyError:
        raise MissingConfiguration(
            "Missing environment variables: "
            "CW_DB_TEST_USER, CW_DB_TEST_PASSWORD, "
            "CW_DB_TEST_SERVER"
        )

    import pyodbc

    pyodbc.connect(
        generate_connection_string(
            SERVER,
            USER,
            PASS
        ),
        readonly=True
    )

    # import sqlalchemy
    # from sqlalchemy.engine import URL

    # url = URL.create(
    #     drivername="mssql+pyodbc",
    #     username=USER,
    #     password=PASS,
    #     host="https://" + SERVER,
    #     database="",
    #     query={
    #         "driver" : "ODBC Driver 18 for SQL Server",
    #         "Encrypt" : "yes",
    #         "TrustServerCertificate" : "yes"
    #     }
    # )

    # print(url)

    # engine = sqlalchemy.create_engine(url)

    # conn = engine.connect()
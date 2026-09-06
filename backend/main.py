from cwio import CargoReader, CargoWriter
from fastapi import FastAPI
from pandas import DataFrame
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello world!"}

@app.get("/test_read")
async def test_read(
    production : bool = True
):
    reader = CargoReader(production)

    result : DataFrame = reader.query(
        "SELECT TOP 5 SC_FileName, SC_Date FROM dbo.StorageDocs WHERE SC_DocType = 'POD' ORDER BY SC_Date DESC;"
    )

    return result.to_dict()

@app.get("/test_write")
async def test_write(
    production : bool = False
):
    from cwio.schemas import Activity, UniversalActivity

    writer = CargoWriter(production)

    result : BaseModel = writer.post(
        UniversalActivity(
            activity=Activity(
                summary = "TEST SUMMARY",
                description = "TEST DESCRIPTION"
            )
        )
    )

    return result.model_dump()

    



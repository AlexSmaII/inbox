from cwio import CargoReader, CargoWriter
from fastapi import FastAPI, HTTPException
from inbox import PODInbox
from msgraph.generated.models.message import Message
from pandas import DataFrame
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello world!"}

@app.get("/emails")
async def get_emails():
    try:
        inbox = PODInbox()
        emails : list[Message] = await inbox.get_emails()
        return [
            {
                "subject" : e.subject,
                "received" : e.received_date_time,
                "body" : e.body_preview,
                "has_attachments" : e.has_attachments,
                "attachments" : e.attachments
            } for e in emails
        ]
    except Exception as e:
        return HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/test_read")
async def test_read(
    production : bool = True
):
    try:
        reader = CargoReader(production)

        result : DataFrame = reader.query(
            "SELECT TOP 5 SC_FileName, SC_Date FROM dbo.StorageDocs WHERE SC_DocType = 'POD' ORDER BY SC_Date DESC;"
        )

        return result.to_dict()
    
    except Exception as e:

        return HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/test_write")
async def test_write(
    production : bool = False
):
    try:
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
    
    except Exception as e:

        return HTTPException(
            status_code=500,
            detail=str(e)
        )

    



import json

from google import genai
from google.genai import types
from google.genai.types import GenerateContentResponse, UsageMetadata
from PIL import Image
from pydantic import BaseModel

from ..models import Docket, DocketResult
from .base import PODClassifier

client = genai.Client()

MODEL = 'gemini-3.5-flash-lite'

prompt = """
Extract the 
"""

class GeminiPODClassifier(PODClassifier):

    def __init__(self, model : str):
        self.model = model

    def __classify_docket(self, image : Image):
        
        response : GenerateContentResponse = client.models.generate_content(
            model = MODEL,
            contents=[
                types.Part.from_bytes(
                    data=image.tobytes(),
                    mime_type='image/jpeg'
                ),
                prompt
            ],
            config={
                "response_format": {
                    "text": {
                        "mime_type": "application/json",
                        "schema": Docket.model_json_schema
                    }
                }
            }
        )

        response_json_string : str = response.text
        response_json : dict = json.load(response_json_string)

        tokens : UsageMetadata = response.usage_metadata

        tokens_in, tokens_out = tokens.promptTokenCount, tokens.candidatesTokenCount + tokens.thoughtsTokenCount

        response = Docket.model_validate_strings(response_json)

        result = DocketResult.model_validate({
            **Docket.model_dump(),
            tokens_in : tokens_in,
            tokens_out : tokens_out
        })

        return result



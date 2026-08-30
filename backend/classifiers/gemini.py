from io import BytesIO

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    GenerateContentResponse,
    GenerateContentResponseUsageMetadata,
)
from models import Docket, DocketResult
from PIL import Image

from .base import PODClassifier

load_dotenv()
client = genai.Client(vertexai=True)

MODEL = 'gemini-3.5-flash-lite'

prompt = """
Extract the fields:

Shipment code starts with 'S'
Job code starts with 'B'
Consignment code starts with 'T'
Container codes are optional
"""

class GeminiPODClassifier(PODClassifier):

    def __init__(self, model : str) -> None:
        self.model = model

    def _classify_docket(self, image : Image) -> DocketResult:
        bin = BytesIO()
        image.save(bin, format="JPEG")
        image_bytes = bin.getvalue()

        response : GenerateContentResponse = client.models.generate_content(
            model = self.model,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/jpeg'
                )
            ],
            config=GenerateContentConfig(
                temperature=0,
                response_schema=Docket,
                response_mime_type="application/json"
            )
        )

        response_json_string : str = response.text

        tokens : GenerateContentResponseUsageMetadata = response.usage_metadata

        tokens_in, tokens_out = tokens.prompt_token_count or 0, tokens.candidates_token_count or 0 + tokens.thoughts_token_count or 0

        response = Docket.model_validate_json(response_json_string)

        result = DocketResult.model_validate({
            **response.model_dump(),
            "tokens_in" : tokens_in,
            "tokens_out" : tokens_out,
            "model_name" : self.model,
            "model_provider" : "google"
        })

        return result



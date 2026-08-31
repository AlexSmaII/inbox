from io import BytesIO

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    GenerateContentResponse,
    GenerateContentResponseUsageMetadata,
)
from models import Docket, DocketClassification, ModelCall
from PIL import Image

from .base import PODClassifier

load_dotenv()
client = genai.Client(vertexai=True)

PROMPT = """
Extract the fields:

Shipment code starts with 'S' and then is only digits
Job code starts with 'B' and then is only digits
Consignment code starts with 'T' and then is only digits
Container codes are optional and are 11 characters long
""".strip()

class GeminiPODClassifier(PODClassifier):
    """
    Gemini-based POD classifier. Uses one or several
    Gemini models to extract fields from POD dockets.

    If several models are given, each model in the list
    is used to classify the given POD docket until one
    of the models successfully classifies the docket.

    A classification is counted as successful if:
    - There is exactly one shipment, job, or consigmnent number
    - The identification number starts with the correct letter
    - All container codes meet ISO 6346

    Args:
        models (str | list[str]):
            List of Gemini model names to use to classify
            POD dockets (e.g., 'gemini-3.5-flash-lite').
            The first model in the list is used first,
            so it's best to start with a cheaper model
            and use a larger model after that as a
            fallback.
    """

    def __init__(self, models : str | list[str]) -> None:
        if isinstance(models, str): models = [models]
        self.models = models

    def attempt_classify_docket(
        self,
        model : str,
        image_bytes : bytes,
        previous_model_calls : list[ModelCall]
    ) -> DocketClassification:

        response : GenerateContentResponse = client.models.generate_content(
            model = model,
            contents=[
                PROMPT,
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

        model_call = ModelCall(
            tokens_in = tokens.prompt_token_count or 0,
            tokens_out = tokens.candidates_token_count or 0 + tokens.thoughts_token_count or 0,
            model_name = model,
            model_provider = "google"
        )

        model_calls = [*previous_model_calls, model_call]

        response = Docket.model_validate_json(response_json_string)

        result = DocketClassification.model_validate({
            **response.model_dump(),
            "model_calls" : model_calls
        })

        return result


    def _classify_docket(self, image : Image) -> DocketClassification:
        bin = BytesIO()
        image.save(bin, format="JPEG")
        image_bytes = bin.getvalue()

        model_calls : list[ModelCall] = []

        for i, model in enumerate(self.models):

            result = self.attempt_classify_docket(
                model=model,
                image_bytes=image_bytes,
                previous_model_calls = model_calls
            )

            model_calls = result.model_calls

            if result.is_valid:
                break
        
        return result



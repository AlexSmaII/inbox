from datetime import datetime, timedelta
from io import BytesIO
from time import sleep

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    GenerateContentResponse,
    GenerateContentResponseUsageMetadata,
)
from models import (
    Docket,
    DocketBase,
    DocketClassification,
    ModelCall
)
from PIL import Image

from .base import PODClassifier

load_dotenv()
client = genai.Client(vertexai=True)

MAX_RETRIES  = 3
RETRY_COOLDOWN = 20

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
        previous_model_calls : list[ModelCall],
        retries : int = MAX_RETRIES,
        retry_cooldown : timedelta = timedelta(seconds=RETRY_COOLDOWN)
    ) -> DocketClassification:

        for i in range(retries):

            response_json_string = None

            try:
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
                        response_schema=DocketBase,
                        response_mime_type="application/json"
                    )
                )

                response_json_string : str = response.text

                tokens : GenerateContentResponseUsageMetadata = response.usage_metadata

                response = DocketBase.model_validate_json(response_json_string)

                model_call = ModelCall(
                    tokens_in = tokens.prompt_token_count or 0,
                    tokens_out = tokens.candidates_token_count or 0 + tokens.thoughts_token_count or 0,
                    model_name = model,
                    model_provider = "google"
                )

                model_calls = [*previous_model_calls, model_call]

                result = DocketClassification.model_validate({
                    **response.model_dump(),
                    "model_calls" : model_calls
                })

                return result

            except Exception as e:
                timestamp = datetime.now().strftime("%H:%M:%S")
                secs = retry_cooldown.total_seconds()

                message = f"{timestamp}: "

                if response_json_string:
                    message += f"Received illegal response from {model}. "
                else: message += f"Call to {model} failed. "

                message += f"Retrying in {secs:.0f} seconds. "
                message += f"{retries - i} attempt(s) remaining. "

                print(message.strip())

                if response_json_string:
                    print(response_json_string)
                
                print(f"Traceback: {e!s}")
                
                if i == retries - 1:
                    raise e
            
            finally:
                sleep(retry_cooldown.total_seconds())


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



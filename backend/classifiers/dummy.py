from models import DocketResult
from PIL import Image

from .base import PODClassifier


class DummyPODClassifier(PODClassifier):

    def _classify_docket(self, image : Image) -> DocketResult:
        return DocketResult(
            shipment_code = 'S12345678',
            job_code = None,
            consignment_code = None,
            consol_code = 'C12345678',
            container_codes = [],
            tokens_in = 0,
            tokens_out = 0
        )



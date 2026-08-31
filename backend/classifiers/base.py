from abc import ABC, abstractmethod
from pathlib import Path

from models import DocketClassification, DocketResult
from PIL import Image
from preprocess import extract_pod_image


class PODClassifier(ABC):

    @abstractmethod
    def _classify_docket(self, image : Image) -> DocketClassification:
        pass
    
    def classify_docket(self, path : Path) -> DocketResult:
        image : Image = extract_pod_image(path)
        pred = self._classify_docket(image)
        return DocketResult.model_validate({
            **pred.model_dump(),
            "file_name": path.name
        })
    
    def classify_dockets(self, paths : list[Path]) -> list[DocketResult]:
        return [self.classify_docket(path) for path in paths]

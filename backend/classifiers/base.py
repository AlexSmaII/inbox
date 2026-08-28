from abc import ABC, abstractmethod
from pathlib import Path

from models import DocketResult
from PIL import Image
from preprocess import extract_pod_image


class PODClassifier(ABC):

    @abstractmethod
    def _classify_docket(self, image : Image) -> DocketResult:
        pass
    
    def classify_docket(self, path : Path) -> DocketResult:
        image : Image = extract_pod_image(path)
        return self._classify_docket(image)
    
    def classify_dockets(self, paths : list[Path]) -> list[DocketResult]:
        return [self.classify_docket(path) for path in paths]

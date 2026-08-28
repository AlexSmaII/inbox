from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image

from ..models import DocketResult
from ..preprocess import extract_pod_images


class PODClassifier(ABC):

    @abstractmethod
    def __classify_docket(self, image : Image) -> DocketResult:
        pass
    
    def classify_docket(self, path : Path) -> DocketResult:
        image : Image = extract_pod_images(path)
        return self.__classify_docket(self, image)
    
    def classify_dockets(self, paths : list[Path]) -> list[DocketResult]:
        return [self.classify_docket(path) for path in paths]

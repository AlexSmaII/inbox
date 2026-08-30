from pathlib import Path

from classifiers.base import PODClassifier
from classifiers.dummy import DummyPODClassifier
from classifiers.gemini import GeminiPODClassifier
from dataset import load_dataset
from models import DocketResult
from pydantic_evals import Dataset
from pydantic_evals.reporting import EvaluationReport

DATASET_PATH : Path = Path(__file__).parent / "data" / "labels.json"
RESULT_PATH  : Path = Path(__file__).parent / "data" / "result.json"
dataset = load_dataset()
classifier_dummy = DummyPODClassifier()
classifier_gemini = GeminiPODClassifier("gemini-3.5-flash-lite")


def slice_dataset(dataset : Dataset, len : int) -> Dataset:
    return Dataset(
        name=dataset.name,
        cases=dataset.cases[:len],
        evaluators=dataset.evaluators
    )


def evaluate(dataset : Dataset[Path, DocketResult, None], strategy : PODClassifier):
    # Shrink base dataset
    dataset : Dataset = slice_dataset(dataset, 3)

    def classify(path : Path):
        return strategy.classify_docket(path)
        #return Docket.model_validate(result.model_dump())


    report : EvaluationReport = dataset.evaluate_sync(classify)

    # report_json = report.model_dump_json(indent=4)

    # with open(RESULT_PATH, "w", encoding="utf-8") as f:
    #     f.write(report_json)

    report.print(include_output=True, include_expected_output=True)


if __name__ == "__main__":
    evaluate(dataset, GeminiPODClassifier("gemini-3.5-flash-lite"))
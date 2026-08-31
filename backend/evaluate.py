import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from classifiers.base import PODClassifier
from classifiers.dummy import DummyPODClassifier
from classifiers.gemini import GeminiPODClassifier
from dataset import load_dataset
from models import DocketResult
from pydantic_evals import Dataset
from pydantic_evals.reporting import EvaluationReport

DATASET_PATH : Path = Path(__file__).parent / "data" / "labels.json"
RESULT_PATH  : Path = Path(__file__).parent / "data" / "result.csv"
dataset = load_dataset()
classifier_dummy = DummyPODClassifier()
classifier_gemini = GeminiPODClassifier("gemini-3.5-flash-lite")


def slice_dataset(dataset : Dataset, len : int) -> Dataset:
    return Dataset(
        name=dataset.name,
        cases=dataset.cases[:len],
        evaluators=dataset.evaluators
    )


def serialise_result(
    report : EvaluationReport
) -> list[dict[str, str]]:
    result : list[dict] = []

    mean_cost = np.mean([c.output.cost for c in report.cases])
    mean_time = np.mean([c.total_duration for c in report.cases])

    for case in report.cases:
        pred : DocketResult = case.output
        true : DocketResult  = case.expected_output

        result.append({
            "File Name": true.file_name,
            "Cost": f"${(pred.cost):.6f}",
            "Seconds": f"{case.total_duration:.2f}",
            "Attempts": f"{pred.models_used}",
            "Tokens In": f"{pred.tokens_in}",
            "Tokens Out": f"{pred.tokens_out}",
            "Predicted Number": pred.identifier,
            "True Number": true.identifier,
            "Predicted Container Number": ", ".join(pred.container_codes) or "N/A",
            "True Container Number": ", ".join(true.container_codes) or "N/A"
        })
    
    result.append({
            "File Name": "AVERAGE PER 1000 POD'S",
            "Cost": f"${(mean_cost * 1000):.2f}",
            "Seconds": f"{mean_time * 1000:.2f}"
    })

    return result


def export_result(
    result : EvaluationReport,
    out_path : Path
):
    result_dict = serialise_result(result)
    pd.DataFrame(result_dict).to_csv(out_path, index=False)
    print(f"Result saved to file: {out_path}")


def evaluate(dataset : Dataset[Path, DocketResult, None], strategy : PODClassifier):
    # Shrink base dataset
    # dataset : Dataset = slice_dataset(dataset, 10)

    def classify(path : Path):
        return strategy.classify_docket(path)
        #return Docket.model_validate(result.model_dump())


    report : EvaluationReport = dataset.evaluate_sync(classify)

    # report_json = report.model_dump_json(indent=4)

    # with open(RESULT_PATH, "w", encoding="utf-8") as f:
    #     f.write(report_json)

    report.print(include_output=True, include_expected_output=True)

    export_result(report, RESULT_PATH)


if __name__ == "__main__":
    models = [
        "gemini-2.5-flash-lite",
        "gemini-3.5-flash-lite"
    ]

    evaluate(dataset, GeminiPODClassifier(models))
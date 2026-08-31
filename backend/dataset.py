from dataclasses import dataclass
from pathlib import Path

from models import Docket, DocketFile, DocketResult
from pydantic import TypeAdapter
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

DATASET_PATH : Path = Path(__file__).parent / "data" / "labels.json"

dataset_adapter = TypeAdapter(list[DocketFile])


@dataclass
class Correct(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        pred : Docket = ctx.output
        return pred.is_valid


@dataclass
class ExactMatch(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        pred : Docket = ctx.output
        true : Docket = ctx.expected_output

        if pred.identifier != true.identifier: return False
        if pred.consol_code != true.consol_code: return False
        if sorted(pred.container_codes) != sorted(true.container_codes): return False
        return True


@dataclass
class CostPerThousand(Evaluator):
    def evaluate(self, ctx : EvaluatorContext) -> float:
        pred : DocketResult = ctx.output
        return pred.cost * 1000


def load_dataset(
    path : Path = DATASET_PATH
) -> Dataset[Path, DocketResult, None]:
    with open(path, "r", encoding="utf-8") as f:
        docket_files : list[DocketFile] = dataset_adapter.validate_json(f.read())

    incorrect_dockets = [d for d in docket_files if not d.is_valid]
    if len(incorrect_dockets) > 0:
        raise ValueError(
            f"The following dockets are invalid: {[d.index for d in incorrect_dockets]}"
        )

    dataset = Dataset[Path, DocketResult, None](
        name="pod_dockets",
        cases = [
            Case(
                name=d.path,
                inputs=Path(d.path),
                expected_output=DocketResult.model_validate(
                    {
                        **d.model_dump(),
                        "tokens_in" : 0,
                        "tokens_out" : 0
                    }
                )
            ) for d in docket_files
        ],
        evaluators=[
            ExactMatch(),
            CostPerThousand()
        ]
    )

    return dataset


if __name__ == "__main__":
    print(load_dataset().model_dump_json(indent=4))
from pathlib import Path

from models import Docket, DocketFile
from pydantic import TypeAdapter
from pydantic_evals import Case, Dataset

DATASET_PATH : Path = Path(__file__).parent / "data" / "labels.json"

dataset_adapter = TypeAdapter(list[DocketFile])

def load_dataset(
    path : Path = DATASET_PATH
):
    with open(path, "r", encoding="utf-8") as f:
        dockets : list[DocketFile] = dataset_adapter.validate_json(f.read())

    incorrect_dockets = [d for d in dockets if not d.is_valid]
    if len(incorrect_dockets) > 0:
        raise ValueError(
            f"The following dockets are invalid: {[d.index for d in incorrect_dockets]}"
        )

    dataset = Dataset[Path, Docket, None](
        name="pod_dockets",
        cases = [
            Case(
                name=d.path,
                inputs=Path(d.path),
                expected_output=Docket.model_validate(d.model_dump())
            ) for d in dockets
        ]
    )

    return dataset


if __name__ == "__main__":
    print(load_dataset().model_dump_json(indent=4))
import json
import random
import shutil
from pathlib import Path

from natsort import natsorted

DATA_PATH   : Path = Path(__file__).parent / "data"
FILE_PATH   : Path = DATA_PATH / "population"
SAMPLE_PATH : Path = DATA_PATH / "sample"
SAMPLE_SIZE : int = 75
EXPORT_FILE : Path = DATA_PATH / "labels.json"

def generate_sample_data() -> None:
    if SAMPLE_PATH.exists():
       shutil.rmtree(SAMPLE_PATH)
    SAMPLE_PATH.mkdir(exist_ok=True, parents=True)

    files = natsorted([f for f in FILE_PATH.iterdir()])

    dataset_sample = random.sample(files, SAMPLE_SIZE)

    for file in dataset_sample:
        new_path = SAMPLE_PATH.joinpath(file.name)
        shutil.copy(file, new_path)


def label_samples(
    retain_progress : bool = True
) -> None:
    data : list[dict[str, str|None]] = []
    if EXPORT_FILE.exists():
        if retain_progress:
            with open(EXPORT_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
        else:
            EXPORT_FILE.unlink()
    files = natsorted([i for i in SAMPLE_PATH.iterdir()])
    files = files[len(data):]
    for i, file in enumerate(files, start=len(data)):
        print(f"File #{i+1:03d}: {file.name}")
        identifier       = input("Enter shipment / job / consignment code (starts with S or B or T):")
        consol           = input("Enter CONSOL code (starts with C, leave blank if not given):      ")
        container_string = input("Enter comma-separated container codes (leave blank if not given): ")

        identifier = identifier.upper().strip()

        shipment_code = identifier if identifier.startswith("S") else None
        job_code = identifier if identifier.startswith("B") else None
        consignment_code = identifier if identifier.startswith("T") else None

        consol = consol.upper().strip()
        if consol == "": consol = None
        containers = container_string.upper().strip().replace(" ", "").split(",")
        if container_string == "": containers = []

        data.append({
            "index" : i,
            "path" : str(file.resolve()),
            "shipment_code" : shipment_code,
            "job_code" : job_code,
            "consignment_code" : consignment_code,
            "consol_code" : consol,
            "container_codes" : containers
        })
        with open(EXPORT_FILE, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=4)
    print(f"Saved to {EXPORT_FILE.resolve()}")

if __name__ == "__main__":
    # generate_sample_data()
    label_samples()

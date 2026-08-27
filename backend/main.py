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
        shipment  = input("Enter shipment / job code (starts with S or B): ")
        container = input("Enter container code (leave blank if not given):")
        if container == "": container = None

        data.append({
            "index" : i,
            "path" : str(file.resolve()),
            "shipment_code" : shipment,
            "container_code" : container
        })
        with open(EXPORT_FILE, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=4)
    print(f"Saved to {EXPORT_FILE.resolve()}")

if __name__ == "__main__":
    # generate_sample_data()
    label_samples()

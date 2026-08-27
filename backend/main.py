import json
import random
import shutil
from pathlib import Path

FILE_PATH   : Path = Path("../.data")
SAMPLE_PATH : Path = Path("../.sample")
SAMPLE_SIZE : int = 75
EXPORT_PATH : Path = Path("../.dataset/data.json")

def generate_sample_data() -> None:
    if SAMPLE_PATH.exists():
        shutil.rmtree(SAMPLE_PATH)
    SAMPLE_PATH.mkdir(exist_ok=True, parents=True)

    files = [f for f in FILE_PATH.iterdir()]

    dataset_sample = random.sample(files, SAMPLE_SIZE)

    for file in dataset_sample:
        new_path = SAMPLE_PATH.joinpath(file.name)
        shutil.copy(file, new_path)


def label_samples() -> None:
    if EXPORT_PATH.parent.exists():
        shutil.rmtree(EXPORT_PATH.parent)
    EXPORT_PATH.parent.mkdir(exist_ok=True, parents=True)
    data : list[dict[str, str|None]] = []
    files = [i for i in SAMPLE_PATH.iterdir()]
    for i, file in enumerate(files):
        print(f"File #{i:03d}: {file.name}")
        shipment  = input("Enter shipment / job code (starts with S):      ")
        container = input("Enter container code (leave blank if not given):")
        if container == "": container = None

        data.append({
            "path" : str(file.resolve()),
            "shipment_code" : shipment,
            "container_code" : container
        })
    with open(EXPORT_PATH, "w", encoding="utf-8") as out:
        json.dump(data, out, indent=4)
    print(f"Saved to {EXPORT_PATH.resolve()}")

if __name__ == "__main__":
    generate_sample_data()
    label_samples()

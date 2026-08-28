import json
from pathlib import Path
import re

import numpy as np
from pydantic import BaseModel, TypeAdapter
from pydantic_evals import Case, Dataset

DATASET_PATH : Path = Path(__file__).parent / "data" / "labels.json"

class Docket(BaseModel):
    index : int
    path : str
    shipment_code : str | None
    job_code : str | None
    consignment_code : str | None
    consol_code : str | None
    container_codes : list[str]

    @property
    def identifier(self) -> str:
        identifier = self.shipment_code or self.job_code or self.consignment_code or self.consol_code
        if not identifier: raise ValueError("Docket does not have an identifier")
        return identifier

    @property
    def is_valid(self) -> bool:
        
        def validate_container_code(code : str) -> bool:
            code_without_check_digit = code[:-1]

            alphabet = '0123456789A BCDEFGHIJK LMNOPQRSTU VWXYZ'
            check_digit_value = str(sum(
                alphabet.index(n) * pow(2, i)
                for i, n in enumerate(code_without_check_digit)
            ) % 11 % 10)

            return code[-1] == check_digit_value

        for code in self.container_codes:
            if not re.match(r"[A-Z]{3}[U|J|Z]\d{7}", code): return False
            if not validate_container_code(code): return False

        if self.shipment_code    and not re.match(r"S\d{8}", self.shipment_code    or ""): return False
        if self.job_code         and not re.match(r"B\d{8}", self.job_code         or ""): return False
        if self.consignment_code and not re.match(r"T\d{8}", self.consignment_code or ""): return False

        primary_identifiers = [self.shipment_code, self.job_code, self.consignment_code]
        valid_primary_identifiers = sum(1 for i in primary_identifiers if i is not None)
        if valid_primary_identifiers > 1: return False
        return True



dataset_adapter = TypeAdapter(list[Docket])

def load_dataset(
    path : Path = DATASET_PATH
):
    with open(path, "r", encoding="utf-8") as f:
        dockets = dataset_adapter.validate_json(f.read())

    #is_valid = [d.is_valid for d in dockets]
    #print(np.unique(is_valid, return_counts=True))
    [print(f"{d.path}: {d.container_codes}") for d in dockets if not d.is_valid]
    #raise NotImplementedError()


def purify_dataset():
    raise NotImplementedError


if __name__ == "__main__":
    load_dataset()
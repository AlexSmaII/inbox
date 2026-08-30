import re

from genai_prices import Usage, calc_price
from pydantic import BaseModel


class Docket(BaseModel):
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


class DocketFile(Docket):
    index : int
    path : str


class DocketResult(Docket):
    tokens_in : int
    tokens_out : int
    model_name : str | None = None
    model_provider : str | None = None

    @property
    def cost(self) -> float:
        if not self.model_name or not self.model_provider:
            return 0
        
        return calc_price(
            Usage(
                input_tokens=self.tokens_in,
                output_tokens=self.tokens_out
            ),
            model_ref=self.model_name,
            provider_id=self.model_provider
        ).total_price

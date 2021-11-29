from ..core import EDIParser
import pytest
from pathlib import Path
from os import getcwd

testing_dir = Path(__file__).parents[0]
x12_850 = testing_dir / "samples/x12/sample_850.edi"

class TestEDIParser():
    def test_isa_parser(self):
        parser = EDIParser()
        print(x12_850.read_text())
        isa = parser._parse_isa(x12_850.read_text())
        print(f"{isa.__dict__=}")
        assert not isa
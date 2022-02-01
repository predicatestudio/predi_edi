from ..edi import X12Decoder
from ..core import load
import pytest
from pathlib import Path
from os import getcwd

testing_dir = Path(__file__).parents[0]
x12_850 = testing_dir / "samples/x12/850/sample_amz_850.edi"


class TestEDIDecoder:
    def test_stability(self):
        testpath = Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/sample_targetds_850.edi")
        data = load(testpath.open())

        with testpath.open("r") as fp:
            pdata = data.as_x12()
            rdata = fp.read()
            assert pdata == rdata

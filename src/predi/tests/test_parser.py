from ..edi import X12Decoder
import pytest
from pathlib import Path
from os import getcwd

testing_dir = Path(__file__).parents[0]
x12_850 = testing_dir / "samples/x12/850/sample_amz_850.edi"


class TestEDIDecoder:
    def test_isa_decoder(self):
        decoder = X12Decoder()
        parsed = decoder.parse(x12_850)
        assert False
        decoder = X12Decoder()
        pprint((decoder.parse(x12_path).seg_len))

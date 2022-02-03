from predi import edi
from .. import edi
from ..core import load, dump
import pytest
from pathlib import Path
from os import getcwd
from . import TEST_DIR, SAMPLE_DIR, FIXTURE_DIR

x12_850 = TEST_DIR / "samples/x12/850/sample_amz_850.edi"


def test_load_and_dump():
    for standard_dir in SAMPLE_DIR.iterdir():
        s_standard = edi.Standards[standard_dir.stem].value
        for trans_dir in standard_dir.iterdir():
            for edi_file in trans_dir.iterdir():
                if edi_file.suffix == s_standard.file_suffix:
                    for f_standard in [st.value for st in edi.Standards if not st.name == s_standard.name]:

                        fixture_file = FIXTURE_DIR / s_standard.name / f_standard.name / trans_dir.stem / str(edi_file.stem + f_standard.file_suffix)
                        fixture_file.parent.mkdir(parents=True, exist_ok=True)
                        fixture_file.touch()
                        with fixture_file.open("r") as ff, edi_file.open("r") as sf:
                            # Get the decoder from the Standard based on dir structure
                            sample_doc = load(sf, decoder=s_standard.decoder)
                            fixture_doc = load(ff, decoder=f_standard.decoder)
                            for s_attr, f_attr in zip(sample_doc.get_defining_attributes(soft=True), fixture_doc.get_defining_attributes(soft=True)):
                                assert s_attr == f_attr


# class TestEDIDecoder:

#     def test_stability(self):
#         testpath = Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/sample_targetds_850.edi")
#         data = load(testpath.open())

#         with testpath.open("r") as fp:
#             pdata = data.as_x12()
#             rdata = fp.read()
# assert pdata == rdata

from pathlib import Path

from predi import edi
from predi.core import dump, load
from . import TEST_DIR

SAMPLES_DIR = TEST_DIR / "samples"
FIXTURES_DIR = TEST_DIR / "fixtures"

DECODERS = {
    "x12": edi.X12Decoder,
    # "json": edi.PREDIDecoder_JSON
}

ENCODERS = {
    "x12": edi.X12Encoder,
    "json": edi.PREDIEncoder_JSON
}

def main():
    write_loaded_fixtures()


def write_loaded_fixtures():
    for standard_dir in SAMPLES_DIR.iterdir():
        for trans_dir in standard_dir.iterdir():
            for edi_file in trans_dir.iterdir():
                if edi_file.suffix == ".edi":
                    for standard, encoder in [(s, e) for s,e in ENCODERS.items() if not s==standard_dir]:

                        fixture_file = FIXTURES_DIR / standard_dir.stem / standard / trans_dir.stem / str(edi_file.stem + ".predi")
                        fixture_file.parent.mkdir(parents=True, exist_ok=True)
                        fixture_file.touch()
                        with fixture_file.open("w") as wf, edi_file.open("r") as rf:
                            doc = load(rf)
                            dump(doc, wf, encoder=encoder())


if __name__ == "__main__":
    main()

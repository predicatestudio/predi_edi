from predi import edi
from predi.core import dump, load

from . import FIXTURE_DIR, SAMPLE_DIR


def main():
    write_loaded_fixtures()


def write_loaded_fixtures():
    for standard_dir in SAMPLE_DIR.iterdir():
        s_standard = edi.Standards[standard_dir.stem].value
        for trans_dir in standard_dir.iterdir():
            for edi_file in trans_dir.iterdir():
                if edi_file.suffix == s_standard.file_suffix:
                    for f_standard in [st.value for st in edi.Standards if not st.name == s_standard.name]:

                        fixture_file = FIXTURE_DIR / s_standard.name / f_standard.name / trans_dir.stem / str(edi_file.stem + f_standard.file_suffix)
                        fixture_file.parent.mkdir(parents=True, exist_ok=True)
                        fixture_file.touch()
                        with fixture_file.open("w") as wf, edi_file.open("r") as rf:
                            # Get the decoder from the Standard based on dir structure
                            doc = load(rf, decoder=s_standard.decoder)
                            dump(doc, wf, encoder=f_standard.encoder)


if __name__ == "__main__":
    main()

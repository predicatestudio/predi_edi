from typing import TextIO, cast
from pathlib import Path
from pprint import pprint
import json
from .edi import EDI_Decoder, EDI_Document, PrEDIDecoder_JSON, PrEDIEncoder_JSON, X12Decoder, guess_edi_standard, EDI_Encoder, X12Document


def load(fp: TextIO, *, decoder: EDI_Decoder = None) -> EDI_Document:
    s: str = fp.read()
    return loads(
        s,
        decoder=decoder,
    )


def loads(s: str, *, decoder: EDI_Decoder = None) -> EDI_Document:
    if not decoder:
        decoder = guess_edi_standard(s).decoder

    return decoder.decode(s)


def dump(doc: EDI_Document, fp: TextIO, *, encoder: EDI_Encoder | None = None) -> None:
    fp.write(dumps(doc=doc, encoder=encoder))


def dumps(doc: EDI_Document, *, encoder: EDI_Encoder | None = None) -> str:
    """Returns a string EDI encoding based on the Encoder passed. Defaults to X12Encoder"""
    if not encoder:
        encoder = guess_edi_standard(doc).encoder
    return encoder.encode(doc)


def main():
    # print("hello from core")
    testpath = Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/amz.edi")
    fixpath = Path("/home/benjamin/predicatestudio/predi/src/predi/tests/fixtures/x12/json/850/sample_targetds_850.predi")
    data: X12Document = cast(X12Document, load(testpath.open(), decoder=X12Decoder()))
    # fixdata: X12Document = cast(X12Document, load(fixpath.open(), decoder=PrEDIDecoder_JSON()))
    # pprint(dumps(data, encoder=PrEDIEncoder_JSON()))
    # pprint(X12Document.from_yaml(data.as_toml()))
    pprint(X12Document.from_toml(data.as_toml()))
    # for i in range(len(fixdata.flattened_list)):
    #     f_el, d_el = fixdata.flattened_list[i], data.flattened_list[i]
    #     if not (f_el == d_el):
    #         print(f_el)
    #         print(d_el)
    # pprint(fixdata.flattened_list)
    # pprint(data.flattened_list)
    # pprint(json.loads(fixdata.as_json()))

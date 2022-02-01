from curses import raw
import json
from typing import IO, TextIO, cast
import yaml
import markupsafe
from abc import ABC
import dataclasses
import enum
from pathlib import Path
from pprint import pprint
from .edi import EDI_Decoder, EDI_Document, X12Encoder, guess_edi_standard, EDI_Encoder, X12Document
from pydantic import BaseModel


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
    if not encoder:
        encoder = guess_edi_standard(doc).encoder
    return encoder.encode(doc)


def main():
    # print("hello from core")
    testpath = Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/sample_targetds_850.edi")
    data: X12Document = cast(X12Document, load(testpath.open()))
    pprint(data.data)
    import json

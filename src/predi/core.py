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
from .edi import EDI_Decoder, EDI_Document, guess_edi_standard, EDI_Encoder, X12_Document
from pydantic import BaseModel


def load(fp: TextIO, decoder_cls: type[EDI_Decoder] = None):
    s: str = fp.read()
    return loads(
        s,
        decoder_cls=decoder_cls,
    )


def loads(s: str, decoder_cls: type[EDI_Decoder] = None) -> EDI_Document:
    if not decoder_cls:
        decoder_cls = guess_edi_standard(s).decoder
    decoder = cast(EDI_Decoder, decoder_cls())
    return decoder.parses(s)


def dump(fp: TextIO, encoder: EDI_Encoder = None):
    return dumps(
        fp.read(),
        encoder=encoder,
    )


def dumps(s: str, encoder: EDI_Encoder = None):
    pass


def main():
    # print("hello from core")
    testpath = Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/sample_targetds_850.edi")
    data: X12_Document = cast(X12_Document, load(testpath.open()))
    pprint(data.loops[0].as_nested_loops)

from typing import TextIO
from .edi import EDI_Decoder, EDI_Document, EDI_Encoder, guess_edi_standard


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

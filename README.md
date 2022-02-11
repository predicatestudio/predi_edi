# predi_edi

PrEDI EDI is an open standard for EDI created for use in the Predicate Studio suite.

## Why a new EDI Standard?

x12 is proprietary, and EDIFACT, while much better, is still file-based. EDI is not so unique a field that it aught to require its own base technologies, simply new implementations. Thus, PrEDI.

## What is PrEDI?

PrEDI is designed for Predicate Studio, but moreso it is designed for python and modern implementations. To keep with this, PrEDI is simply a standard to format EDI transactions and specifications in JSON. This further allows the data to be written or read in YAML, and it provides easy conversion to markdown or HTML using existing technologies. This provides far more ease for the human user.

## Installation

clone this repo, then, in your python environnement, run:

"""
pip install .
"""

## Use

PrEDI is designed primary to be used as a python library and is modeled after the builtin json library

### As a Python Library

#### Quickstart

parsing is simple

```python
In [1]: from predi.core import load # loads can also be used for strings

In [2]: from pathlib import Path

In [3]: fp = Path("./example.edi")

In [4]: doc = load(fp.open("r"))
WARNING:root:Guessing EDI standard. guess: x12

In [5]: # This returns an EDI_Document object, a subclass of list

In [6]: print(doc)
[[['ISA', ... '000069737']]]
```

so is encoding

```python
In [7]: from predi.core import dump, dumps

In [8]: from predi.edi import get_standard

In [9]: j_encoder = get_standard("json").encoder

In [12]: # EDI_Encoder objects can be passed to load(s) and dump(s) to ensure accurate encoding and decoding

In [11]: with Path("./edixample.json").open("w") as f:
    ...:     dump(doc, f, encoder=j_encoder)

In [12]: # dump to a file, nearly identical to builtin json lib

In [13]: print(dumps(doc, encoder=j_encoder))
{
  "x12_delimiters": [
    "*",
    ">",
    "~"
  ],
  "x12": [
    [
      [
        "ISA",
        "00",
        ...
      ],
        ...
    ]
  ]
}

In [15]: # or dumps to a string.
```

### CLI

The CLI is not a core part of this library and is still in progress, but feel free to check it out with:

```bash
predi --help
```

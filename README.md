# predi_edi

PrEDI EDI is an open standard for EDI created for use in the Predicate Studio suite.

## Why a new EDI Standard?

x12 is proprietary, and EDIFACT, while much better, is still file-based. EDI is not so unique a field that it ought to require its own base technologies, simply new implementations. Thus, PrEDI.

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

Parsing an x12 document requires two documents:

1. The Mapping (in the form of a python or json file)
2. The EDI document (an x12 document)

Once you have these two, you can begin parsing. First, import your mapping and load an X12_Mapper object from it.

```python
# From a json file
from pathlib import Path
from predi.transactions import load_mapping
mapping_file = Path(./path/to/mapping.json)
a_mapping = load_mapping(mapping_file)

# Or import directly from a python file

from my_mappings import a_mapping

# Generate a Mapper
from predi.transactions import X12_Mapper
mapper = X12_Mapper(a_mapping)
```

Once you have an X12_Mapper object you can parse an x12 transaction.

```python
from predi.api import load

x12_file = Path(./path/to/x12.edi)
order = mapper.parser_data(load(x12_file.open()))
```

Mapping files are best created in python, then exported to json for sharing or storage.
They are built on pydantic Models, so they can be exported by calling the .json() method with any argument that might be passed to a pydantic Model. Reccomended kwargs include indent=2 and exclude_defaults=True for readable and condensed files, respectively.

```python
save_file = Path("path/to/my/saved/mapping.json")
save_file.write_text(a_mapping.json(indent=2, exclude_defaults=True))
```

### CLI

The CLI is not a core part of this library and is still in progress, but feel free to check it out with:

```bash
predi --help
```

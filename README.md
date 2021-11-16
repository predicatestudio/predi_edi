# predi_edi
PrEDI EDI is an open standard for EDI created for use in the Predicate Studio suite.

## Why a new EDI Standard?
x12 is proprietary, and EDIFACT, while much better, is still file-based. EDI is not so unique a field that it aught to require its own base technologies, simply new impletmentations. Thus, PrEDI. 

## What is PrEDI?
PrEDI is designed for Predicate Studio, but moreso it is designed for python and modern implementations. To keep with this, PrEDI is simply a standard to format EDI transactions and specifications in JSON. This further allows the data to be written or read in YAML, and it provides easy conversion to markdown or HTML using existing technologies. This provides far more ease for the human user.

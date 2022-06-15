from pathlib import Path
from pprint import pprint
import json
from predi.core import load

from predi.edi import X12Decoder
from predi.transactions.mapping.x12 import X12_Mapper

# REAL __init__ start


def main():
    from predi.transactions.mapping.amz_850 import amazon850map

    X12_PATH = "/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/amz_ex.edi"
    with Path(X12_PATH).open("r") as f:
        x12_doc = load(f)
    mapper = X12_Mapper(amazon850map)
    order = mapper.parse(x12_doc)
    pprint(order)
    # tomlkit.dump(model2.schema(as_toml=True), raw_model.open("w"))

    Path("temp.json").touch()
    with Path("temp.json").open("w") as tempf:

        json.dump(json.loads(amazon850map.json(exclude_defaults=True)), tempf, indent=2)

if __name__ == "__main__":
    main()

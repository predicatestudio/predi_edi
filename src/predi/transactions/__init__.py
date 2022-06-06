from pathlib import Path
from pprint import pprint
import json

from predi.edi import X12Decoder
from predi.transactions.maps.x12 import X12_Mapper
# from .specs.amz_850 import amazon850Spec

from .models import PrediTransactionModel
from .maps import X12BasePredimaps

# REAL __init__ start



def main():
    from predi.transactions.maps.amz_850 import amazon850map
    X12_PATH = "/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/amz_ex.edi"
    raw_input = Path(X12_PATH).read_text()    # model2 = base_models.BasePurchaseOrder
    decoder = X12Decoder()
    x12_doc=decoder.decode(raw_input)
    mapper=X12_Mapper(amazon850map)
    order = mapper.parse(x12_doc)
    pprint(order)
    # tomlkit.dump(model2.schema(as_toml=True), raw_model.open("w"))
    
    Path("temp.json").touch()
    with Path("temp.json").open("w") as tempf:
        
        json.dump(json.loads(amazon850map.json(exclude_defaults=True)), tempf, indent=2)
    # pprint(model2.__fields__)
    # pprint(model.__fields__)

    # for k, v in s1[key].items():
    #     if k not in s2[key].keys():
    #         pprint(k)
    # pprint(v)
    # for k in s1[key]:
    #     print(k)
    # print(s1[key][k] == s1[key][k])
    # spec = Spec(raw_spec)
    # trans_data = spec.decode(raw_input)
    # model = PrediTransactionModel.from_toml("transaction_model_path")
    # transaction = model.create_transaction(trans_data)
    # print(transaction.as_toml())

    # x12 = core.load(Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/amz_ex.edi").open("r"))  # Raw edi -> EDI trans
    # spec = TransactionTemplate.load(Path("temp/temp.toml"))  # partner spec

    # trans_data = spec.parse(x12.transactions)  # Transaction Data

    # from ..models import PrediTransactionModel
    # from ..models.amz import AmazonPO

    # model = PrediTransactionModel.from_toml(
    #     Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/schemas/predi_transactions/amz_purchase_order.toml")
    # )  # Transaction Model
    # # pprint(model.schema())
    # # pprint(AmazonPO.schema())
    # with Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/schemas/predi_transactions/amz_po.toml").open("w") as f:
    #     tomlkit.dump(AmazonPO.schema(), f)

    # decoder = TransactionDecoder({"AMZ_PO": AmazonPO})
    # decoder.decode(trans_data)


if __name__ == "__main__":
    main()

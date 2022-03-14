from pathlib import Path
from pprint import pprint

from predi.transactions.specs.amz_850 import Amazon850Spec

from .models import PrediTransactionModel
from .specs import TransactionTemplate, X12TransactionList

PrediTransactionModel
# REAL __init__ start
TransactionTemplate


def main():
    X12_PATH = "/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/amz_ex.edi"
    SPEC_PATH = "src/predi/transactions/specs/amz_850.toml"
    MODEL_PATH = "src/predi/transactions/models/base_purchase_order.toml"
    raw_input = Path(X12_PATH).read_text()
    raw_spec = Path(SPEC_PATH)
    raw_model = Path(MODEL_PATH)
    # model2 = base_models.BasePurchaseOrder
    # tomlkit.dump(model2.schema(as_toml=True), raw_model.open("w"))
    model = PrediTransactionModel.from_toml(raw_model)
    spec = TransactionTemplate.load(raw_spec)
    print(Amazon850Spec)
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

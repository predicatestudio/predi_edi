from abc import ABC
from enum import Enum
from pathlib import Path
from pprint import pprint
from typing import Optional

import tomlkit
from pydantic import create_model, validator

from ...utils import PrediBaseModel, create_model_from_schema, python_from_toml


class PrediTransactionType(Enum):
    PurchaseOrder = "PurchaseOrder"
    ShipConfirm = "ShipConfirm"
    Custom = "Custom"
    # TODO Incomplete


class PrediLoop(PrediBaseModel):
    """A Loop for containing nested, often repeatable data (e.g., ItemLoops)"""

    pass


class PrediFields(PrediBaseModel):
    """Contains all fields (i.e., non-metadata) for PrediTransactions"""

    pass


class PrediTransactionModel(PrediBaseModel, ABC):
    """An abstract Base Model for all Predi Transaction Models
    If
    """

    transaction_type: str
    fields: PrediFields

    @classmethod
    def create_transaction_model(cls, schema: dict, transaction_collection: Enum = None):
        """Parses a schema from a python dict to create a transaction model for decoding, encoding, and storing transaction data.
        If no transaction collection is passed, BaseTransactionCollection is used.
        """
        collection = transaction_collection or BaseTransactionCollection
        trans_type = schema["properties"]["transaction_type"]["default"]
        trans_type_model = collection[trans_type]
        sub_models = {}
        definitions = schema["definitions"]
        # for _, definition in schema.pop("definitions").items():
        #     sub_model = create_model_from_schema(definition, __base__=PrediBaseModel, __definitions__=definitions)
        trans_model = create_model_from_schema(schema, __base__=PrediBaseModel)
        return trans_model

    @classmethod
    def from_toml(cls, schema_file: Path, transaction_collection: Enum = None):
        """Parses a schema from a toml document to create a transaction model for decoding, encoding, and storing transaction data.
        If no transaction collection is passed, BaseTransactionCollection is used.
        Wraps 'create_transaction_model'
        """
        with schema_file.open("r") as f:
            schema = python_from_toml(tomlkit.load(f))
        return cls.create_transaction_model(schema, transaction_collection=transaction_collection)


# Base PO
class POItemData(PrediLoop):
    KEY: str
    assigned_id: int
    order_quant: int
    unit_price: float
    unit_price_basis_code: Optional[str]
    uom: str
    upc_ean_consumer_pack_code: Optional[str]


class PurchaseOrderFields(PrediFields):
    trans_set_id: str
    customer_ref_num: str
    order_type: str
    po_num: str
    po_date: str
    ship_to: str
    no_deliver_after: str
    no_deliver_before: str
    sale_req_code: str
    seg_count: str
    trans_set_ctrl_num: str
    trans_set_purpose_code: str
    line_item_count: str
    item_data: POItemData


class BasePurchaseOrder(PrediTransactionModel):
    transaction_type: str = "PurchaseOrder"
    fields: PurchaseOrderFields

    @validator("transaction_type")
    def validate_is_purchase_order(cls, v: str):
        if not v.lower() == "purchaseorder":
            raise ValueError("PurchaseOrder Transaction Models must have 'transaction_type' of 'PurchaseOrder'")
        return v.trim()


# Custom
class CustomTransaction(PrediTransactionModel):
    pass


# Collection of Base Transactions
class BaseTransactionCollection(Enum):
    PurchaseOrder = BasePurchaseOrder
    Custom = CustomTransaction

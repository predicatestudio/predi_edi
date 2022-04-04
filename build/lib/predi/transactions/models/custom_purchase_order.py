from . import BasePurchaseOrder, PurchaseOrderFields


class CustomPO(BasePurchaseOrder):
    transaction_type: str = "PurchaseOrder"
    fields: PurchaseOrderFields

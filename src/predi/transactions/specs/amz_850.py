from . import X12TransactionList

class AmazonSpec():
    ...

class Amazon850Spec(X12TransactionList.x850.value, AmazonSpec):
    pass

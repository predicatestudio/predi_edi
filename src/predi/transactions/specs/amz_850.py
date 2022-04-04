from predi.transactions.specs.x12 import CodedOptions, Element, Loop, Segment
from pydantic import PrivateAttr

from . import X12TransactionList


class AmazonSpec:
    ...


amz_850_components = [
    Segment(
        id="ST",
        name="transaction_set_header",
        required=True,
        max_use=1,
        elements=[
            Element(
                id=1,
                name="transaction_set_identifier_code",
                required=True,
                options=CodedOptions(
                    values={850: "purchase_order"},
                ),
            ),
            Element(id=2, name="transaction_set_control_number", required=True),
        ],
    ),
    Segment(
        id="BEG",
        name="beginning_segment_for_purchase_order",
        required=True,
        max_use=1,
        elements=[
            Element(
                id=1,
                name="transaction_set_purpose_code",
                options=CodedOptions(values={00: "original"}, exhaustive=False),
            ),
            Element(
                id=2,
                name="purchase_order_type_code",
                required=True,
                options=CodedOptions(
                    values={
                        "CN": "consigned_order",
                        "NE": "new_order",
                        "NP": "new_product_information",
                        "RO": "rush_order",
                    }
                ),
            ),
            Element(
                id=3,
                name="purchase_order_number",
                required=True,
                options=None,
            ),
            Element(
                id=4,
                name="date",
                required=True,
                options=None,
            ),
        ],
    ),
    Segment(id="REF", name="reference_identification_01", required=True, max_use=None, elements=[]),
    Segment(id="REF", name="reference_identification_02", required=False, max_use=None, elements=[]),
    Segment(id="FOB", name="fob_related_instructions", required=False, max_use=None, elements=[]),
    Segment(id="CSH", name="sales_requirements", required=True, max_use=5, elements=[]),
    Segment(id="DTM", name="datetime_reference_01", required=False, max_use=10, elements=[]),
    Segment(id="DTM", name="datetime_reference_02", required=False, max_use=10, elements=[]),
    Segment(id="PKG", name="marking_packageing_loading", required=False, max_use=200, elements=[]),
    Loop(
        id="N9",
        name="note_loop",
        required=True,
        max_use=1000,
        components=[
            Segment(id="N9", name="reference_identification", required=True, max_use=1, elements=[]),
            Segment(id="N9", name="message_text", required=True, max_use=1000, elements=[]),
        ],
    ),
    Loop(id="N1", name="name_loop", required=True, max_use=200, components=[Segment(id="N1", name="name", required=True, max_use=1, elements=[])]),
    Loop(
        id="PO1",
        name="line_item_loop",
        required=True,
        max_use=100000,
        components=[
            Segment(id="PO1", name="baseline_item_data", required=True, max_use=1, elements=[]),
        ],
    ),
    Loop(
        id="CTT",
        name="transaction_totals_loop",
        required=True,
        max_use=1,
        components=[
            Segment(id="CTT", name="transaction_totals", required=True, max_use=1, elements=[]),
        ],
    ),
    Segment(id="SE", name="transaction_set_trailer", required=True, max_use=1, elements=[]),
]

amazon850spec = X12TransactionList.X12_850.value(title= "amz_850",components=amz_850_components)

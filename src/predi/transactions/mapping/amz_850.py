from datetime import date, datetime

from predi.transactions.mapping.x12 import BlankElement, CodedOptions, Element, Loop, NestingRules, QualifiedElement, Reference, Segment

from . import X12BasePredimaps


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
                options=CodedOptions(values={"00": "original"}, exhaustive=False),
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
                    },
                    # decode=False
                ),
            ),
            Element(
                id=3,
                name="purchase_order_number",
                required=True,
                options=None,
            ),
            BlankElement(id=4),
            Element(
                id=5,
                name="date",
                required=True,
                options=None,
            ),
        ],
    ),
    # PDF map holds two REFs in a row. This should be singular since multiple are allowed.
    Segment(
        id="REF",
        name="reference_identification_01",
        required=True,
        max_use=None,
        elements=[
            Element(
                id=1,
                name="reference_identification_qualifier",
                required=True,
                # reference_tag="reference_identification_qualifier_1",
                options=CodedOptions(
                    values={"CR": "customer_reference_number", "PD": "promotion_number"},
                    exhaustive=False,
                ),
            ),
            QualifiedElement(
                id=2,
                name="reference_identification",
                qualifier_tag="reference_identification_qualifier",
                required=True,
                options=None,
            ),
        ],
    ),
    Segment(
        id="FOB",
        name="fob_related_instructions",
        max_use=None,
        elements=[
            Element(
                id=1,
                name="shipping_method_of_payment",
                required=True,
                options=CodedOptions(
                    values={
                        "BP": "Paid by Buyer",
                        "CC": "Collect",
                        "DF": "Defined by Buyer and Seller",
                        "FO": "FOB Port of Call",
                        "PP": "Prepaid (by Seller)",
                        "PS": "Paid by Seller)",
                    },
                    exhaustive=False,
                ),
            ),
            Element(
                id=2,
                name="transportation_terms_qualifier",
                # reference_tag="transportation_terms_qualifier",
                options=CodedOptions(
                    values={"01": "incoterms"},
                    exhaustive=False,
                ),
            ),
            QualifiedElement(
                id=3,
                name="transportation_terms",
                qualifier_tag="transportation_terms_qualifier",
                options=CodedOptions(
                    values={
                        "CFR": "Cost and Freight",
                        "CIF": "Cost, Insurance, and Freight",
                        "CIP": "Carriage and Insurance Paid To",
                        "CPT": "Carriage Paid To",
                        "DAF": "Delivered at Frontier",
                        "DDP": "Delivered Duty Paid",
                        "DDU": "Deliver Duty Unpaid",
                        "EXW": "Ex Works",
                        "FCA": "Free Carrier",
                        "FOB": "Free on Board",
                    },
                    exhaustive=False,
                ),
            ),
            Element(
                id=4,
                name="location_qualifier",
                # reference_tag="location_qualifier",
                options=CodedOptions(values={"OV": "on_vessel"}, exhaustive=False),
            ),
            QualifiedElement(
                id=5,
                name="location_description",
                qualifier_tag="location_qualifier",
            ),
        ],
    ),
    Segment(
        id="CSH",
        name="sales_requirements",
        required=True,
        max_use=5,
        elements=[
            Element(
                id=1,
                name="sales_requirement_code",
                required=True,
                options=CodedOptions(values={"N": "no_back_order", "Y": "back_order_if_out_of_stock"}, exhaustive=False),
            )
        ],
    ),
    Segment(
        id="DTM",
        name="datetime_reference_01",
        required=False,
        max_use=20,
        elements=[
            Element(
                id=1,
                name="date_time_qualifier_01",
                required=True,
                options=CodedOptions(values={"063": "do_not_deliver_after", "064": "do_not_deliver_before"}, exhaustive=False),
            ),
            QualifiedElement(
                id=2,
                name="date",
                required=True,
                qualifier_tag="date_time_qualifier_01",
            ),
        ],
    ),
    Segment(
        id="PKG",
        name="marking_packaging_loading",
        required=False,
        max_use=200,
        elements=[
            Element(
                id=1,
                name="item_description_type",
                required=True,
                options=CodedOptions(values={"F": "free_form"}, exhaustive=False),
            ),
            Element(
                id=2,
                name="packaging_characteristic_code",
                required=True,
                options=CodedOptions(values={"CS": "container_shape"}, exhaustive=False),
            ),
            Element(
                id=5,
                name="package_description",
                required=True,
                options=None,
            ),
        ],
    ),
    Loop(
        id="N9",
        name="note_loop",
        required=True,
        max_use=1000,
        components=[
            Segment(
                id="N9",
                name="reference_identification",
                required=True,
                max_use=1,
                elements=[
                    Element(
                        id=1,
                        name="reference_identification_qualifier",
                        # reference_tag="reference_identification_qualifier",
                        required=True,
                        options=CodedOptions(values={"L1": "letters_or_notes"}, exhaustive=False),
                    ),
                    QualifiedElement(
                        id=2,
                        name="reference_identification",
                        qualifier_tag="reference_identification_qualifier",
                    ),
                ],
            ),
            Segment(
                id="N9",
                name="message_text",
                required=True,
                max_use=1000,
                elements=[
                    Element(
                        id=1,
                        name="free_form_message_text",
                        required=True,
                        options=None,
                    )
                ],
            ),
        ],
    ),
    Loop(
        id="N1",
        name="name_loop",
        required=True,
        max_use=200,
        nesting=NestingRules(
            name=Reference(reference_name="entity_identifier_code"),
            as_list=False,
        ),
        components=[
            Segment(
                id="N1",
                name="name",
                required=True,
                max_use=1,
                elements=[
                    Element(
                        id=1,
                        name="entity_identifier_code",
                        required=True,
                        options=CodedOptions(values={"ST": "ship_to"}, exhaustive=False),
                    ),
                    BlankElement(id=2),
                    Element(
                        id=3,
                        name="identification_code_qualifier",
                        required=True,
                        # reference_tag="identification_code_qualifier",
                        options=CodedOptions(
                            values={
                                "15": "Standard Address Number",
                                "92": "Assigned by Buyer or Buyer's Agent",
                                "ZZ": "Mutually Defined",
                            },
                            exhaustive=False,
                        ),
                    ),
                    QualifiedElement(
                        id=4,
                        name="identification_code",
                        qualifier_tag="identification_code_qualifier",
                        required=True,
                    ),
                ],
            )
        ],
    ),
    Loop(
        id="PO1",
        name="line_item_loop",
        required=True,
        max_use=100000,
        nesting=NestingRules(name="line_items"),
        components=[
            Segment(
                id="PO1",
                name="baseline_item_data",
                required=True,
                max_use=1,
                elements=[
                    Element(
                        id=1,
                        name="assigned_identification",
                        required=True,
                        options=None,
                    ),
                    Element(
                        id=2,
                        name="quantity_ordered",
                        required=True,
                        options=None,
                    ),
                    Element(
                        id=3,
                        name="unit_or_basis_for_measure_code",
                        required=True,
                        options=CodedOptions(
                            values={"CA": "cases", "EA": "each"},
                            exhaustive=False,
                        ),
                    ),
                    Element(
                        id=4,
                        name="unit_price",
                        required=True,
                        options=None,
                    ),
                    Element(
                        id=5,
                        name="basis_of_unit_price_code",
                        required=True,
                        options=CodedOptions(
                            exhaustive=False,
                            values={
                                "PE": "per_each",
                                "RE": "retail_price_per_each",
                            },
                        ),
                    ),
                    Element(
                        id=6,
                        name="product_service_id_qualifier",
                        # reference_tag="product_service_id_qualifier",
                        required=True,
                        options=CodedOptions(
                            exhaustive=False,
                            values={
                                "BP": "buyers_part_number",
                                "EN": "ean",
                                "IB": "isbn",
                                "UA": "upc_ean_case_code",
                                "UK": "upc_ean_shipping_container_code",
                                "UP": "upc_ean_consumer_package_code",
                                "VN": "vendor_item_number",
                            },
                        ),
                    ),
                    QualifiedElement(
                        id=7,
                        name="product_service_id",
                        qualifier_tag="product_service_id_qualifier",
                        required=True,
                        options=None,
                    ),
                ],
            )
        ],
    ),
    Loop(
        id="CTT",
        name="transaction_totals_loop",
        required=True,
        max_use=1,
        components=[
            Segment(
                id="CTT",
                name="transaction_totals",
                required=True,
                max_use=1,
                elements=[
                    Element(
                        id=1,
                        name="number_of_line_items",
                        required=True,
                        options=None,
                    ),
                    Element(
                        id=2,
                        name="hash_total",
                        required=True,
                        options=None,
                    ),
                ],
            ),
        ],
    ),
    Segment(
        id="SE",
        name="transaction_set_trailer",
        required=True,
        max_use=1,
        elements=[
            Element(
                id=1,
                name="number_of_included_segments",
                required=True,
                options=None,
            ),
            Element(
                id=2,
                name="transaction_set_control_number",
                required=True,
                options=None,
            ),
        ],
    ),
]

amazon850map = X12BasePredimaps.X12_850.value(
    author="amazon",
    title="amz_850",
    version="4010",
    version_date=date(2017, 8, 10),
    predimap_version="0.0.1",
    components=amz_850_components,
)

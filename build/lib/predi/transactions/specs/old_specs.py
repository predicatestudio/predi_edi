import json
from abc import abstractmethod
from pathlib import Path
from pprint import pprint
from typing import Optional

import tomlkit
from pydantic import BaseModel, validator
from tomlkit import TOMLDocument, aot, comment, inline_table, nl, table
from tomlkit.items import AoT, Table

from ... import utils
from ...edi import TransactionSet, X12Segment
from ..models import PrediTransactionModel


class EDITemplateBaseModel(BaseModel):
    @validator("*")
    def convert_toml_items(cls, v):
        """tomlkit rewrites builtins. Other libs (like pydantic) don't know how to deal with them"""
        if isinstance(v, tomlkit.items.Item):
            for builtin in [str, list, dict, int, float]:
                if isinstance(v, builtin):
                    return builtin(v)
        return v

    @abstractmethod
    def toml(self, indent: int = 0) -> Table | TOMLDocument:
        """returns a TOML table representing the component.
        Optional indentation."""


class Element(EDITemplateBaseModel):
    id: str = ""
    required: bool = False
    options: Optional[str | list] = None
    qualifier: Optional[str] = None
    quality: Optional[dict] = None
    multiple: bool = False
    discard: bool = False

    def dict(self, exclude_defaults=True, **kwargs) -> dict:
        d = super().dict(**kwargs, exclude_defaults=exclude_defaults)
        return d  # {key: val for key, val in d.items() if val}

    def toml(self, indent: int = 0) -> Table:
        tab = table().indent(indent)
        for key, val in self.dict().items():
            if isinstance(val, dict) and len(val) < 2:
                tab.add(key, inline_table().add(*val.popitem()))
            else:
                tab.add(key, val)
        return tab


class Component(EDITemplateBaseModel):
    type: str
    id: str
    required: bool = False
    export_key: Optional[str] = None
    export_as: Optional[dict] = None
    delete_after: Optional[list] = None

    @validator("type")
    def validate_type(cls, v):
        if not v == cls.__name__.lower():
            raise ValueError(f"incorrect type {v} for class {cls.__name__}")
        return v

    @abstractmethod
    def metadata(self):
        return self.dict()


class Segment(Component):
    max_use: int = 0  # 0 is no max
    elements: list[Element]

    def toml(self, indent: int = 0) -> Table:
        tab = table().indent(indent)
        # initialize elements aot because tomlkit cant directly convert dicts
        elements: AoT = aot()
        contents = self.dict()
        contents["elements"] = elements

        # convert elements to toml, append all to table
        for el in self.elements:
            el_tab = el.toml(indent + 2)
            elements.append(el_tab)
        for key, val in contents.items():
            if val:
                tab.add(key, val)
        return tab

    def metadata(self):
        return self.dict(exclude={"elements", True})


class Loop(Component):
    repetition: int  # Number of times the loop can repeat
    loop: list[Component]
    name: str

    def __repr__(self) -> str:
        return str(self.loop)

    def toml(self, indent: int = 0) -> Table:
        tab = table().indent(indent)
        # initialize loop aot because tomlkit cant directly convert dicts
        loop: AoT = aot()
        contents = self.dict()
        contents["loop"] = loop

        # convert loop components to toml, add all to table
        for seg in self.loop:
            seg_tab = seg.toml(indent + 2)
            loop.append(seg_tab)
        for key, val in contents.items():
            if val:
                if isinstance(val, dict) and len(val) < 2:
                    val = inline_table().add(*val.popitem())
                tab.add(key, val)
        return tab

    def metadata(self):
        return self.dict(exclude={"loop", True})


class TransactionTemplate(EDITemplateBaseModel):
    transaction_set_id: str
    export_rules: dict
    components: list[Component]

    def couple_to_template(
        self, template_loop: list[Component], transaction_segments: list[X12Segment]
    ) -> tuple[list[tuple] | list, list[X12Segment]]:

        transaction_has_segments = bool(transaction_segments)
        if not transaction_has_segments:
            return (None, None)

        loop_coupling: list[tuple | list] = []
        for loop_component in template_loop:
            loop_component_is_viable = True
            seg = transaction_segments.pop(0)
            while loop_component_is_viable and transaction_has_segments:
                # On a match, couple the element and move on
                if seg.seg_id.lower() == loop_component.id:
                    if isinstance(loop_component, Segment):
                        # Add the coupling, get next seg
                        loop_coupling.append([(loop_component.metadata(), seg[0])] + [*zip(loop_component.elements, seg[1:])])
                        if transaction_has_segments := bool(transaction_segments):
                            seg = transaction_segments.pop(0)
                    # Loops can match multiple elements, so this is a recursive parallel to the Segment case
                    elif isinstance(loop_component, Loop):
                        # put the seg back to pass to recursive call
                        transaction_segments = [seg, *transaction_segments]
                        subloop_coupling, transaction_segments = self.couple_to_template(loop_component.loop, transaction_segments)
                        # Add the coupling, get next seg
                        loop_coupling.append([(loop_component.metadata(), seg[0])] + subloop_coupling)
                        if transaction_has_segments := bool(transaction_segments):
                            seg = transaction_segments.pop(0)
                # If no match, end the loop and put back the seg
                else:
                    loop_component_is_viable = False
                    transaction_segments = [seg, *transaction_segments]
        return (loop_coupling, transaction_segments)

    def parse(self, t: TransactionSet | list[TransactionSet]) -> dict:

        # if not t:
        #     return None
        def flatten(l):
            # flattened = []
            # for item in l:
            #     if isinstance(item, list):
            #         flattened += flatten(item)
            #     else:
            #         flattened.append(item)
            # return flattened
            return [item for sublist in l for item in sublist]

        def map(coupling: list):
            component_export = {}
            mapping = []
            for comp in coupling:
                discard_list = set()

                comp_map = []
                comp_meta = comp.pop(0)[0]
                comp_map.append(comp_meta)

                # Loop
                if comp_meta["type"].lower() == "loop":
                    loop_map, loop_export = map(comp)
                    comp_map.append(loop_map)

                    if exp_dict := comp_meta.get("export_as"):
                        if exp_key := comp_meta.get("export_key"):
                            template_key = exp_dict[loop_export[exp_key]]
                    else:
                        template_key = comp_meta["name"]
                    if other_values := component_export.get(template_key) and template.multiple:
                        try:
                            other_values.append(loop_export)
                        except AttributeError as e:
                            other_values = [other_values, loop_export]
                        loop_export = other_values
                    if delete_list := comp_meta["delete_after"]:
                        for key in delete_list:
                            if key in loop_export:
                                del loop_export[key]
                    component_export[template_key] = loop_export
                # Segment
                else:
                    for template, val in comp:

                        if qualifier_id := template.qualifier:
                            if qualifier_id in component_export:
                                qualified_id = template.quality.get(component_export[qualifier_id])
                                template_key = qualified_id
                            comp_map.append((template, val))
                        # Default mapping is direct id: val
                        else:
                            comp_map.append((template.id, val))

                            template_key = template.id
                        # If multiples are an option and are present, val should be a list.
                        if other_values := component_export.get(template_key) and template.multiple:
                            try:
                                other_values.append(val)
                            except AttributeError as e:
                                other_values = [other_values, val]
                            val = other_values
                        elif other_values := component_export.get(template_key):
                            print(f"{template_key}: {other_values}")

                        component_export[template_key] = val
                        if template.discard or not template_key:
                            # print(f"discarding {template_key}")
                            discard_list.add(template_key)
                mapping.append(comp_map)
                for key in discard_list:
                    del component_export[key]

            return (mapping, component_export)

        if isinstance(t, list):
            return [self.parse(trans) for trans in t]
        coupling, _ = self.couple_to_template(self.components, t.subloops)
        maps, component_export = map(coupling)  # [(type(tup[1]), tup[0]) for tup in flatten(coupling) if isinstance(tup[1], Component)]

        def generate_export(component_export, rules):
            export = {}
            for exp, rule in rules.items():
                if isinstance(rule, dict):
                    pprint(exp)
                    export[exp] = generate_export(component_export[rule["KEY"]], rule)
                if isinstance(rule, str):
                    rule = rule.split(".")
                    if rule[0] == "components":
                        component = component_export.get(rule[1])
                        if isinstance(component, dict):
                            print(f"{rule=}")
                            print(f"{component=}")
                            component = component.get(rule[2])

                        export[exp] = component
            return export

        export = generate_export(component_export, self.export_rules)
        pprint(export)

        return coupling

    def toml(self, indent: int = 0) -> TOMLDocument:
        """Returns a formatted TOMLDocument for storage, sharing, and human readability."""
        # Create doc and add header info
        doc = tomlkit.TOMLDocument()
        doc.add(comment("This is a generated TOML EDI Specification"))
        doc.add(nl())
        doc.add("transaction_set_id", self.transaction_set_id)

        rules = table()
        for k, v in self.export_rules.items():
            rules[k] = v

        doc.add("export_rules", rules)

        # tomlify components into an array of tables https://toml.io/en/v1.0.0#array-of-tables
        spec_components: AoT = aot()
        for component in self.components:
            spec_components.append(component.toml(indent))

        # Add the table to the document and return it
        doc.add("components", spec_components)
        return doc

    @classmethod
    def load_element(cls, element_data: dict) -> Element:
        """Parses an element from a properly formatted dict.

        ex:
        {'id': 'entity_id_code', 'options': 'ST', 'required': True}
        """
        element = Element(**dict(element_data))
        return element

    @classmethod
    def load_segment(cls, segment_data: dict) -> Segment:
        """Parses a segment from a properly formatted dict.

        ex
        {'elements': [Element$see: load_element(), ...]
        'id': 'n1',
        'max_use': 1,
        'required': True,
        'type': 'segment'}
        """
        segment_data["elements"] = [cls.load_element((dict(el))) for el in segment_data.pop("elements")]
        return Segment(**segment_data)

    @classmethod
    def load_loop(cls, loop_data: dict) -> Loop:
        """Parses a loop from a properly formatted dict.

        ex:
        {'id': 'n1',
        'loop': [Segment$see: load_segment, Loop$recursive...],
        'repetition': 1,
        'required': True,
        'type': 'loop'}
        """
        loop_data["loop"] = [cls.load_component(dict(component)) for component in loop_data.pop("loop")]
        return Loop(**loop_data)

    @classmethod
    def load_component(cls, component_data: dict) -> Component:
        """Parses a component (loop or segment) from a properly formatted dict"""
        comp_type = component_data["type"]
        if comp_type == "segment":
            return cls.load_segment(component_data)
        elif comp_type == "loop":
            return cls.load_loop(component_data)
        raise ValueError(component_data)

    @classmethod
    def load(cls, file: Path) -> "TransactionTemplate":
        """Loads an appropriately formatted json or toml file from a pathlib Path.
        Returns a TransactionTemplate for mapping an EDI transaction"""
        with file.open("r") as f:
            return cls.loads(data=f.read(), language=file.suffix.split(".")[-1])

    @classmethod
    def loads(cls, data: str, language: str) -> "TransactionTemplate":
        """Loads an appropriately formatted json or toml string.
        Returns a TransactionTemplate for mapping an EDI transaction"""
        # parse data to dict-like object
        doc: dict[str, list]
        if language == "toml":
            doc = dict(tomlkit.loads(data))
        elif language == "json":
            doc = json.loads(data)
        else:
            raise ValueError(f"{cls.__name__} cannot load data in langauge {language}")
        # create component objects from component data
        doc["components"] = [cls.load_component(dict(component)) for component in doc.pop("components")]
        doc["export_rules"] = utils.python_from_toml(doc.pop("export_rules"))
        template = TransactionTemplate(**doc)
        return template


# class AmazonPOTemplate(PO_Template):
# Header


# Detail

# Summary


class TransactionDecoder:
    def __init__(self, templates):
        self.templates: dict[PrediTransactionModel] = templates

    def decode(self, transaction) -> PrediTransactionModel:  # transaction is any kind of edi transaction
        return self.decode_x12(transaction)

    def decode_x12(self, transaction: TransactionTemplate):
        return transaction


class TransactionEncoder:
    pass


def test_fixtures(template):

    with Path("temp/temp2.toml").open("w") as toml_f, Path("temp/temp.json").open("w") as json_f:
        tomlkit.dump(template.toml(), toml_f)
        json.dump(template.dict(), json_f, indent=2)

    # with Path("temp/temp.json").open("r") as f1, Path("temp/temp2.json").open("r") as f2:
    #     print("comparing json")
    #     i=0
    #     for l1, l2 in zip(f1.readlines(), f2.readlines()):
    #         i+=1
    #         if not l1 == l2:
    #             print(i)
    #             print(l1)
    #             print(l2)
    with Path("temp/temp.toml").open("r") as f1, Path("temp/temp2.toml").open("r") as f2:
        print("comparing toml")
        i = 0
        for l1, l2 in zip(f1.readlines(), f2.readlines()):
            i += 1
            # if not l1 == l2:
            #     # print(i)
            #     # print(l1)
            #     # print(l2)

    for p in ["temp/temp.json", "temp/temp.toml", "temp/temp2.toml"]:
        print(f"comparing to {p}")
        print(template == TransactionTemplate.load(Path(p)))


class EDIBaseModel(BaseModel):
    pass


class EDISpec(EDIBaseModel):
    pass

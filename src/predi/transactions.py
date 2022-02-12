import json
from abc import abstractmethod
from pathlib import Path
from pprint import pprint
from typing import Optional

import tomlkit
from pydantic import BaseModel, validator
from tomlkit import TOMLDocument, aot, comment, nl, table
from tomlkit.items import AoT, Table

from . import core
from .edi import TransactionSet, X12Segment


class Transaction:
    trans_set_code: str
    trans_ctrl_number: int
    trans_length: int

    @classmethod
    def from_x12(cls, trans_set: TransactionSet):
        for transaction_type in cls.__subclasses__():
            if trans_set.transaction_set_code == transaction_type.trans_set_code:
                return transaction_type.from_x12(trans_set)


class PurchaseOrder(Transaction):
    trans_set_code = "850"
    ctrl_num: int
    seg_count: int

    @classmethod
    def from_x12(cls, trans_set: TransactionSet):
        trans = cls()
        for key, el in {
            "trans_set_code": trans_set.transaction_set_code,
            "ctrl_num": trans_set.ctrl_num,
            "seg_count": trans_set.num_subloops,
        }.items():
            trans.__setattr__(key, el)

        # trans.ctrl_num = trans_set.ctrl_num
        # trans.seg_count = trans_set.num_subloops
        return trans

    def __repr__(self) -> str:
        return str(self.__dict__)


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
    id: str
    required: bool = False
    options: Optional[str | list] = None

    def dict(self, **kwargs) -> dict:
        d = super().dict(**kwargs)
        return {key: val for key, val in d.items() if val}

    def toml(self, indent: int = 0) -> Table:
        tab = table().indent(indent)
        for key, val in self.dict().items():
            # if val:
            tab.add(key, val)
        return tab


class Component(EDITemplateBaseModel):
    type: str
    id: str
    required: bool = False

    @validator("type")
    def validate_type(cls, v):
        if not v == cls.__name__.lower():
            raise ValueError(f"incorrect type {v} for class {cls.__name__}")
        return v


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
            tab.add(key, val)
        return tab


class Loop(Component):
    repetition: int  # Number of times the loop can repeat
    loop: list[Component]

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
            tab.add(key, val)
        return tab


class TransactionTemplate(EDITemplateBaseModel):
    transaction_set_id: str
    components: list[Component]

    def map_to_template(
        self, template_loop: list[Component], transaction_segments: list[X12Segment]
    ) -> tuple[list[tuple]|list, list[X12Segment]]:
        if transaction_segments[0].seg_id == 'CTT':
            import ipdb; ipdb.set_trace()
        # print()
        # pprint(transaction_segments)
        # pprint([el.id for el in template_loop])
        transaction_has_segments = bool(transaction_segments)
        if not transaction_has_segments:
            return (None, None)
        
        # print(f"{seg=}")
        # print(type(template_loop[0]))
        # print()
        loop_mapping: list[tuple|list] = []
        for loop_component in template_loop:
            loop_component_is_viable = True
            seg = transaction_segments.pop(0)
            while loop_component_is_viable and transaction_has_segments:
                
                if seg.seg_id == "BEG":
                    import ipdb; ipdb.set_trace()
                # print(f"{seg=}")
                # print(f"{loop_component.id=}")
                if seg.seg_id.lower() == loop_component.id:
                    if isinstance(loop_component, Segment):
                        loop_mapping.append((seg, loop_component))
                        if transaction_segments:
                            seg = transaction_segments.pop(0)
                        else:
                            transaction_has_segments = False
                    elif isinstance(loop_component, Loop):
                        # print(seg)
                        if seg.seg_id == "CTT":
                            import ipdb; ipdb.set_trace()
                        # print(loop_component.loop[0])
                        transaction_segments = [seg, *transaction_segments]
                        # print(f"{transaction_segments=}")
                        subloop_mapping, transaction_segments = self.map_to_template(loop_component.loop, transaction_segments)
                        
                        # print(subloop_mapping)
                        loop_mapping.append(subloop_mapping)
                        if transaction_has_segments := bool(transaction_segments):
                            seg = transaction_segments.pop(0)


                else:
                    loop_component_is_viable = False
                    # if transaction_has_segments:
                    transaction_segments = [seg, *transaction_segments]
        return (loop_mapping, transaction_segments)

    def parse(self, t: TransactionSet | list[TransactionSet]) -> list:
        # if not t:
        #     return None
        if isinstance(t, list):
            return [self.parse(trans) for trans in t]
        # pprint(t)
        mapping, _ = self.map_to_template(self.components, t.subloops)

        return mapping

        # class Temp:
        #     def __init__(self, comps):
        #         self.comps = comps
        #         self.comp = self.comps.pop(0)
        #         self.mapping = []
        # obj = Temp(self.components)

        # def match_component(seg: TransactionSet, obj):
        #     print(f"    {obj.comp.id}")
        #     if seg.seg_id.lower() == obj.comp.id:
        #         obj.mapping.append((seg, obj.comp))
        #     else:
        #         if obj.comps:
        #             obj.comp = obj.comps.pop(0)
        #             match_component(seg, obj)

        # for seg in t:
        #     print(seg.seg_id)
        #     match_component(seg, obj)

        pprint(mapping)

    def toml(self, indent: int = 0) -> TOMLDocument:
        """Returns a formatted TOMLDocument for storage, sharing, and human readability."""
        # Create doc and add header info
        doc = tomlkit.TOMLDocument()
        doc.add(comment("This is a generated TOML EDI Specification"))
        doc.add(nl())
        doc.add("transaction_set_id", self.transaction_set_id)

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
        template = TransactionTemplate(**doc)
        return template


class PO_Template(TransactionTemplate):
    transaction_set_id = "850"


# class AmazonPOTemplate(PO_Template):
# Header


# Detail

# Summary


def test_fixtures(template):
    with Path("temp2.toml").open("w") as toml_f, Path("temp2.json").open("w") as json_f:
        tomlkit.dump(template.toml(), toml_f)
        json.dump(template.dict(), json_f, indent=2)

    with Path("temp.json").open("r") as f1, Path("temp2.json").open("r") as f2:
        print("comparing json")
        for l1, l2 in zip(f1.readlines(), f2.readlines()):
            if not l1 == l2:
                print(l1)
                print(l2)
    with Path("temp.toml").open("r") as f1, Path("temp2.toml").open("r") as f2:
        print("comparing toml")
        for l1, l2 in zip(f1.readlines(), f2.readlines()):
            if not l1 == l2:
                print(l1)
                print(l2)

    for p in ["temp.json", "temp2.json", "temp.toml", "temp2.toml"]:
        print(f"comparing to {p}")
        print(template == TransactionTemplate.load(Path(p)))


def main():
    x12 = core.load(Path("/home/benjamin/predicatestudio/predi/src/predi/tests/samples/x12/850/amz_ex.edi").open("r"))
    template = TransactionTemplate.load(Path("temp.toml"))
    # test_fixtures(template)
    # pprint(template.components)
    parsed = template.parse(x12.transactions)
    pprint(parsed)

def quickprint(parsed):
    for p in parsed:
        if isinstance(p, list):
            quickprint(p)
        else:
            pprint(p[1].id)

if __name__ == "__main__":
    main()

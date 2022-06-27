import json
from pathlib import Path

from predi.transactions.mapping.x12 import X12_Mapper, X12BaseModel, X12PrediMap
from predi.utils import get_nested_subclasses


def load_mapping(mapping: Path | str | dict):

    if isinstance(mapping, Path):
        mapping = json.load(mapping.open())
    elif isinstance(mapping, str):
        mapping = json.loads(mapping)
    assert isinstance(mapping, dict)
    def load_list_of_components(component_list: list[dict]):
        loaded_components = []
        for component in component_list:
            if isinstance(component, dict):
                component = load_component(component)
            loaded_components.append(component)
        return loaded_components

    def load_component(component: dict):
        if not (component_type := component.get("_type")):
            return component
        del component["_type"]
        component_class_obj = get_nested_subclasses(X12BaseModel)[component_type]
        for key, val in component.items():
            if isinstance(val, dict):
                component[key] = load_component(val)
            elif isinstance(val, list):
                component[key] = load_list_of_components(val)
        return component_class_obj(**component)

    loaded_components = [load_component(component) for component in mapping.pop("components")]
    return X12PrediMap(**mapping, components=loaded_components)

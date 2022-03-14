from typing import Any

import tomlkit
import tomlkit.items as toml_items
from pydantic import BaseModel, create_model, validator
from tomlkit.toml_document import TOMLDocument

# TOML compatibly upgrades
class PrediBaseModel(BaseModel):
    """A Predi specific wrapping of Pydantic's BaseModel"""

    @classmethod
    def schema(cls, as_toml: bool = False, **kwargs) -> dict[str, Any]:
        """Wraps Pydantic's BaseModel .schema() with an added option to export as toml"""
        if not as_toml:
            return super().schema(**kwargs)
        return TomlDoc.from_dict(super().schema(**kwargs))

    @validator("*")
    def convert_toml_items(cls, v):
        """tomlkit rewrites builtins. Other libs (like pydantic) don't know how to deal with them.
        This validator purges tomlkit's Items"""
        if isinstance(v, tomlkit.items.Item):
            return python_from_toml(v)
        return v

    def toml(self, indent: int = 0) -> toml_items.Table | TOMLDocument:
        """returns a TOML table representing the component.
        Optional indentation."""  # TODO implement indent
        return TomlDoc.from_dict(self.dict())


def python_to_toml(obj):
    """Converts python builtins to tomlkit Items"""
    if isinstance(obj, (str, int, bool, float)):
        return obj
    elif isinstance(obj, (list, tuple)):
        ar = tomlkit.array([python_to_toml(el) for el in obj])
        return tomlkit.array(ar)

    elif isinstance(obj, (dict)):
        tab = tomlkit.table()
        for key, val in obj.items():
            tab.add(key, python_to_toml(val))
        return tab


def python_from_toml(obj):
    """Converts tomkit Items to python builtins"""
    if not isinstance(obj, (toml_items.Item, TOMLDocument)):
        return obj
    for builtin_type in [str, int, bool, float]:
        if isinstance(obj, builtin_type):
            return builtin_type(obj)

    # Arrays
    if isinstance(obj, toml_items.Array):
        return [python_from_toml(item) for item in obj]

    # Tables and docs
    elif isinstance(obj, (toml_items.Table, TOMLDocument)):
        return {key: python_from_toml(val) for key, val in obj.items()}
    else:
        raise ValueError(f"TOML object {obj} of type {type(obj)} was not adapted")


class TomlDoc(TOMLDocument):
    """A wrapper of TOMLDocument with some helper functions to play better with other kinds of
    python containers.
    """

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the TomlDocument"""
        return python_from_toml(self)

    @classmethod
    def from_dict(cls, d) -> "TomlDoc":
        """Creates a TomlDoc from a dictionary"""
        doc = cls()
        for key, val in d.items():
            doc.add(key, python_to_toml(val))
        return doc


# Schema Parsing
def create_model_from_schema(schema, __base__, __definitions__=None):
    """Converts a schema, as generated from a model, and converts it into a pydantic model
    Reccomended __base__ is PrediBaseModel
    __definitions__ are for schemas without a definitions (e.g., one pulled from a definition.
    """
    name = schema.pop("title")
    docstr = schema.get("description")
    props = {}
    for key_val, prop in schema["properties"].items():
        # Create referenced submodels
        if ref := prop.get("$ref"):
            if not __definitions__:
                __definitions__ = schema["definitions"]
            # Ugly, but functionally pulls the right definition. TODO look at reference standard.
            ref_schema = __definitions__[ref.split("/")[-1]]
            referenced_class = create_model_from_schema(ref_schema, __base__=__base__, __definitions__=__definitions__)
            # Add as field arg
            # TODO Default or optional fields are unaccounted for here
            props[key_val] = (referenced_class, ...)
        # Create 'field' tuples for create_model
        else:
            default_value = prop.get("default")
            type_value = json_to_python_type_conversion(prop["type"])
            # None is passed for optionals without defaults, Elipsis for required.
            if not default_value and key_val in schema["required"]:
                default_value = ...

            props[key_val] = (type_value, default_value)

    mod = create_model(name, **props, __base__=__base__)
    if docstr := schema.get("description"):
        mod.__doc__ = docstr
    return mod


def json_to_python_type_conversion(obj_type):
    """Converts json types to python type callables"""
    TYPE_DICT = {
        "string": str,
        "integer": int,
        "number": float,
    }
    return TYPE_DICT.get(obj_type) or obj_type

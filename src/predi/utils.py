from pydantic import BaseModel


class PrediBaseModel(BaseModel):
    """A Predi specific wrapping of Pydantic's BaseModel"""

    ...


def get_nested_subclasses(parent_class):
    classes = {}
    for subclass in parent_class.__subclasses__():
        classes.update(get_nested_subclasses(subclass))
        classes.update({subclass.__name__: subclass})
    return classes

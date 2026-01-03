from dataclasses import fields
from functools import wraps


def alias_init(cls):
    orig_init = cls.__init__

    @wraps(orig_init)
    def new_init(self, *args, **kwargs):
        # print(kwargs)
        mod_kwargs = {}
        for i in fields(cls):
            alias = i.metadata.get("alias")
            if alias is not None and alias in kwargs:
                mod_kwargs[i.name] = kwargs.get(alias)
            if i.name in kwargs:
                mod_kwargs[i.name] = kwargs.get(i.name)
        orig_init(self, *args, **mod_kwargs)

    cls.__init__ = new_init
    return cls

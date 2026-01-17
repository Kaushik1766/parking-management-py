
from typing import Type
from functools import wraps
from typing import cast

from httpx import get


def singleton(cls_: Type):
    instance = None
    initialized = False

    # @wraps(cls)
    # def get_instance(*args, **kwargs):
    #     nonlocal instance
    #     if instance is None:
    #         instance = cls(*args, **kwargs)
    #     return instance

    class wrapper(cls_):
        @wraps(cls_.__new__)
        def __new__(cls, *args, **kwargs):
            nonlocal instance
            if instance is None:
                instance = super(wrapper, cls).__new__(cls, *args, **kwargs)
            return instance

        @wraps(cls_.__init__)
        def __init__(self, *args, **kwargs):
            nonlocal initialized
            if not initialized:
                super(wrapper, self).__init__(*args, **kwargs)
                initialized = True

    return wrapper
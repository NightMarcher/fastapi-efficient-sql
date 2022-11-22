from abc import ABCMeta


class Singleton(ABCMeta):
    """
    Singleton metaclass, using by:

    >>> class Parent(BaseClass, metaclass=Singleton):pass
    >>> class Child(Parent):pass
    """
    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if not self.__instance:
            self.__instance = super().__call__(*args, **kwargs)
        return self.__instance

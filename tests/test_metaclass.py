from unittest import TestCase

from fastapi_esql import Singleton


class Parent(metaclass=Singleton):
    pass


class Child(Parent):
    pass


class TestSingleton(TestCase):

    def test_inheritance(self):
        c0, c1 = Child(), Child()
        assert c0 is c1

    def test_parent_and_child(self):
        p0, p1 = Parent(), Parent()
        c = Child()
        assert p0 is p1
        assert p0 is not c

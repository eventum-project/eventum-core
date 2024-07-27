from eventum_plugins.metaclasses import Singleton


class A(metaclass=Singleton):
    def __init__(self) -> None:
        self.attr = []


def test_singleton():
    a1 = A()
    a2 = A()

    assert a1 is a2
    assert a1.attr is a2.attr

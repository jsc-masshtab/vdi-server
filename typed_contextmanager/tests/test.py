

from typed_contextmanager import typed_contextmanager



@typed_contextmanager
def ctx(x) -> int:
    yield x


@ctx(3)
def f(n: int):
    return n


def test():
    assert f() == 3
    assert g() == '__'


@typed_contextmanager
def ctx2(x) -> str:
    yield f'_{x}'

@ctx2('_')
def g(x: str):
    return x

from typing import Union

@typed_contextmanager.factory
def main(x, cls: Union[int, str]):
    if issubclass(cls, int):
        return ctx(x)
    if issubclass(cls, str):
        return ctx2(x)
    assert 0


@main('')
def h(n: str):
    return n


def test_factory():
    assert h() == '_'
import pytest

from classy_async.classy_async import g_tasks, g

from dataclasses import dataclass

@dataclass()
class Score(g_tasks.Var):
    # KEY = 'var-1'

    value: int


def test_threadlocal():
    g.use_threadlocal()
    Score(1).set()
    score = Score.get()
    assert score.value == 1


def test_contextvar():
    g.use_threadlocal(False)
    Score(1).set()
    score = Score.get()
    assert isinstance(score, Score)
    assert score.value == 1
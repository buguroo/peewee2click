import pytest


def test_package():
    try:
        import peewee2click
    except ImportError as exc:
        assert False, exc

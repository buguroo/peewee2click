import datetime

from hypothesis import assume, given
from hypothesis.strategies import dates, text
import pytest


@pytest.mark.wip
@given(text())
def test_random_invalid_date_doesnt_work(s):
    """
    This test checks that given random input string that is not a valid date,
    then the function _date_string_to_date will raise a ValueError.
    """

    from peewee2click import _date_string_to_date

    try:
        datetime.datetime.strptime(s, '%Y-%m-%d').date()
    except:
        pass
    else:
        # If it is a valid date, discard it
        assume(False)

    with pytest.raises(ValueError):
        _date_string_to_date(s)


@pytest.mark.wip
@given(dates())
def test_random_valid_date_works_properly(d):
    """
    This test checks that given random input string that is a valid date,
    then the function _date_string_to_date will returns it as a date object
    """

    from peewee2click import _date_string_to_date

    assert _date_string_to_date(d.strftime('%Y-%m-%d')) == d

from click.testing import CliRunner
import click
import peewee
import pytest


class FakeModel(peewee.Model):
    test_date = peewee.DateField()


@pytest.mark.parametrize("invalid_date", [
    '2017',
    '2017-01',
    '2017-01-01 00:00:00',
    '2017-13-01',
    '2017-12-32',
])
def test_date_param_type_doesnt_accept_invalid_strings(invalid_date):
    """
    This test checks that with the decorator click_options_from_model_fields
    you can't pass a date string that is not in the form 'YYYY-MM-DD' to a
    param of type `date`.
    """

    from peewee2click import CRUDL

    @CRUDL.click_options_from_model_fields(FakeModel)
    @click.command()
    def click_func(**kwargs):
        pass

    runner = CliRunner()
    result = runner.invoke(click_func, ["--test-date", invalid_date])
    assert result.exit_code != 0


def test_date_param_type_accepts_valid_strings():
    """
    This test checks that with the decorator click_options_from_model_fields
    you can pass a date string that has the format YYYY-MM-DD to a param of
    type `date`.
    """

    from peewee2click import CRUDL

    @CRUDL.click_options_from_model_fields(FakeModel)
    @click.command()
    def click_func(**kwargs):
        pass

    runner = CliRunner()
    result = runner.invoke(click_func, ["--test-date", '2017-01-01'])
    assert result.exit_code == 0

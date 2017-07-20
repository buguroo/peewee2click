from click.testing import CliRunner
import click
import peewee

# Related to this GH issue: https://github.com/buguroo/peewee2click/issues/3


class RelatedModel(peewee.Model):
    id = peewee.CharField(primary_key=True)


class FakeModel(peewee.Model):
    related = peewee.ForeignKeyField(RelatedModel)


def test_foreign_key_field_has_real_db_type():
    """
    This test checks that a ForeignKey accepts as parameter its field
    type in the related model (char) instead of the default ForeignKey
    peewee type (which is int).

    https://github.com/buguroo/peewee2click/issues/3
    """

    from peewee2click import CRUDL

    @CRUDL.click_options_from_model_fields(FakeModel)
    @click.command()
    def click_func(**kwargs):
        pass

    runner = CliRunner()
    result = runner.invoke(click_func, ['--related', "random_text"])
    assert result.exit_code == 0

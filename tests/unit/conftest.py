from peewee import *
import pytest


@pytest.fixture
def crudl_mock_model():

    sqlite_db = SqliteDatabase(":memory:")

    class CRUDLMockModel(Model):
        id = PrimaryKeyField()
        text_attr = TextField()
        char_attr = CharField()
        fk_attr = ForeignKeyField('self', null=True)
        int_attr = IntegerField(help_text="Just your average integer")
        bool_attr = BooleanField()
        float_attr = FloatField(null=True)

        class Meta:
            database = sqlite_db

    sqlite_db.create_tables([CRUDLMockModel])

    return CRUDLMockModel

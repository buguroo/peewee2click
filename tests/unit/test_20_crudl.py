from unittest.mock import ANY, MagicMock, patch
import re

from click.testing import CliRunner
from peewee import BareField
from peewee import BlobField
from peewee import DateField
from peewee import DateTimeField
from peewee import TimeField
import click
import pytest


def test_print_table_return_table_in_tabulate_format():
    """
    Este test comprueba que el método `print_table` llama una vez a `tabulate`
    con los parámetros apropiados y después usa su salida para imprimirla por
    pantalla usando `click.echo`
    """

    from peewee2click import CRUDL
    tabulate_func = 'peewee2click.tabulate'
    echo_func = 'peewee2click.click.echo'
    with patch(tabulate_func) as tabulate_mock, patch(echo_func) as echo_mock:
        CRUDL.print_table("mock", foo="bar")

    tabulate_mock.assert_called_once_with("mock", tablefmt=CRUDL.TABLEFMT,
                                          foo="bar")
    echo_mock.assert_called_once_with(
        "\n{}\n".format(tabulate_mock.return_value))


def test_format_single_element():
    """
    Este test comprueba que el método `format_single_element` devuelve una
    lista de campos de un elemento formateados de la manera apropiada
    """

    from peewee2click import CRUDL

    element = MagicMock()

    res = CRUDL.format_single_element(element, ['foo', 'bar', 'baz'])
    assert res == [
        ('foo', repr(element.foo)),
        ('bar', repr(element.bar)),
        ('baz', repr(element.baz)),
    ]


def test_format_multiple_elements():
    """
    Este test comprueba que el método `format_multiple_element` devuelve una
    lista de listas de campos de varios elementos formateados de la manera
    apropiada
    """

    from peewee2click import CRUDL

    e1, e2, e3 = MagicMock(), MagicMock(), MagicMock()
    elements = [e1, e2, e3]

    res = CRUDL.format_multiple_elements(elements, ['foo', 'bar', 'baz'])

    assert res == [
        [repr(e1.foo), repr(e1.bar), repr(e1.baz)],
        [repr(e2.foo), repr(e2.bar), repr(e2.baz)],
        [repr(e3.foo), repr(e3.bar), repr(e3.baz)],
    ]


@pytest.mark.parametrize("param,value,exit_code", [
    ("--text-attr", "whatever", 0),
    ("--char-attr", "whatever", 0),
    ("--fk-attr", 1, 0),
    ("--int-attr", 1, 0),
    ("--bool-attr", True, 0),
    ("--float-attr", 1.1, 0),
    ("--id", "whatever", 2),
])
def test_click_options_from_model_fields_accept_each_param(param, value,
                                                           exit_code,
                                                           crudl_mock_model):
    """
    Este test comprueba que con el decorador click_options_from_model_fields
    se generan opciones para cada uno de los atributos excepto para el
    de tipo primary key
    """

    from peewee2click import CRUDL

    @CRUDL.click_options_from_model_fields(crudl_mock_model)
    @click.command()
    def click_func(**kwargs):
        pass

    runner = CliRunner()
    result = runner.invoke(click_func, [param, value])
    assert result.exit_code == exit_code


def test_click_options_from_model_fields_skips_fields(crudl_mock_model):
    """
    Este test comprueba que con el decorador click_options_from_model_fields
    no se generan opciones para especificar los atributos para aquellos campos
    pasados en el párametro skip del decorador
    """

    from peewee2click import CRUDL

    @CRUDL.click_options_from_model_fields(crudl_mock_model,
                                           skip=["bool_attr"])
    @click.command()
    def click_func(**kwargs):
        pass

    runner = CliRunner()
    result = runner.invoke(click_func, ["--bool-attr", True])
    assert result.exit_code != 0


@pytest.mark.parametrize("field_type", [
    DateTimeField,
    DateField,
    TimeField,
    BlobField,
    BareField,
])
def test_click_options_from_model_fields_sets_to_str_field_unknown_peewee_type(
        crudl_mock_model, field_type):
    """
    Este test comprueba que la función click_options_from_model_fields crea
    una opción de `click` de tipo `str` para lost tipos de `peewee`
    `DateTimeField`, `DateField`, `TimeField`, `BlobField` y `BareField`,
    es decir , aquellos que no tienen una equivalencia directa con int, bool,
    str, float o None
    """

    from peewee2click import CRUDL

    class CrudlMockModelWithUnknownField(crudl_mock_model):
        test_attr = field_type()

    with patch('peewee2click.click.option') as option_mock:
        @CRUDL.click_options_from_model_fields(CrudlMockModelWithUnknownField)
        def click_func(**kwargs):
            pass

    option_mock.assert_any_call("--test-attr", type=str, help=ANY)


@pytest.mark.parametrize("param,exit_code", [
    ("--float-attr-set-null", 0),
    ("--text-attr-set-null", 2),
    ("--char-attr-set-null", 2),
    ("--fk-attr-set-null", 0),
    ("--int-attr-set-null", 2),
    ("--bool-attr-set-null", 2),
])
def test_click_options_from_model_fields_add_null_options(
        param, exit_code, crudl_mock_model):
    """
    Este test comprueba que con el decorador click_options_from_model_fields
    no se generan opciones adicionales terminadas en `-set-null` para aquellos
    campos que no tengan el atributo null, mientras que sí se generan para
    aquellos atributos en los que éste está a True
    """

    from peewee2click import CRUDL

    @CRUDL.click_options_from_model_fields(crudl_mock_model)
    @click.command()
    def click_func(**kwargs):
        pass

    runner = CliRunner()
    result = runner.invoke(click_func, [param])
    assert result.exit_code == exit_code


@pytest.mark.parametrize("param,param_type,help_text", [
    ('--int-attr', 'INTEGER', 'Just your average integer'),
    ('--text-attr', 'TEXT', 'No help. Please, document the model.'),
    ('--char-attr', 'TEXT', 'No help. Please, document the model.'),
    ('--fk-attr', 'INTEGER', 'No help. Please, document the model.'),
    ('--bool-attr', 'BOOLEAN', 'No help. Please, document the model.'),
    ('--float-attr', 'FLOAT', 'No help. Please, document the model.'),
])
def test_click_options_from_model_generates_proper_help_strings(
        param, param_type, help_text, crudl_mock_model):
    """
    Este test comprueba que con el decorador click_options_from_model_fields
    se genera un texto de ayuda estándar para aquellos campos que no tengan
    atributo help, mientras que usa el atributo help para aquellos campos
    que lo tengan definido
    """

    from peewee2click import CRUDL

    @CRUDL.click_options_from_model_fields(crudl_mock_model)
    @click.command()
    def click_func(**kwargs):
        pass

    runner = CliRunner()
    result = runner.invoke(click_func, ["--help"])
    assert re.search(
        r'\s*{}\s*{}\s*{}'.format(param, param_type, help_text),
        result.output)


def test_create_method_creates_object_when_force(crudl_mock_model):
    """
    Este test comprueba que el método `create` crea un objeto en base de datos
    cuando se le pasa el parámetro `force=True`
    """

    from peewee2click import CRUDL

    CRUDL.create(crudl_mock_model, force=True,
                 text_attr="mock", char_attr="", int_attr=1, bool_attr=True)
    assert crudl_mock_model.select().where(
        crudl_mock_model.text_attr == "mock").exists()


def test_create_method_asks_for_confirmation_when_no_force():
    """
    Este test comprueba que el método `create` pregunta al usuario la
    confirmación usando el método `click.confirm` cuando el parámetro
    `force` es False
    """

    from peewee2click import CRUDL

    with patch('peewee2click.click.confirm') as click_mock:
        CRUDL.create(MagicMock(), False)
    click_mock.assert_called_once()


def test_create_method_creates_object_when_confirm_is_true(crudl_mock_model):
    """
    Este test comprueba que el método `create` crea un objeto en base de datos
    cuando la respuesta a `click.confirm` es True
    """

    from peewee2click import CRUDL

    with patch('peewee2click.click.confirm', return_value=True):
        CRUDL.create(crudl_mock_model, force=False,
                     text_attr="mock", char_attr="", int_attr=1,
                     bool_attr=True)
    assert crudl_mock_model.select().where(
        crudl_mock_model.text_attr == "mock").exists()


def test_create_method_doesnt_create_object_when_confirm_is_false(
        crudl_mock_model):
    """
    Este test comprueba que el método `create` no crea un objeto en base de
    datos cuando la respuesta a `click.confirm` es False
    """

    from peewee2click import CRUDL

    with patch('peewee2click.click.confirm', return_value=False):
        CRUDL.create(crudl_mock_model, force=False,
                     text_attr="mock", char_attr="", int_attr=1,
                     bool_attr=True)
    assert not crudl_mock_model.select().where(
        crudl_mock_model.text_attr == "mock").exists()


def test_show_method_returns_false_if_not_existing_object(crudl_mock_model):
    """
    Este test comprueba que el método `show` devuelve False cuando se le pasa
    el pk de un objeto no existente
    """

    from peewee2click import CRUDL

    assert CRUDL.show(crudl_mock_model, 1) is False


def test_show_method_returns_true_if_existing_object(crudl_mock_model):
    """
    Este test comprueba que el método `show` devuelve True cuando se le pasa
    el pk de un objeto existente
    """

    from peewee2click import CRUDL

    CRUDL.create(crudl_mock_model, force=True,
                 text_attr="mock", char_attr="", int_attr=1, bool_attr=True)
    assert CRUDL.show(crudl_mock_model, 1) is True


def test_show_method_prints_object_with_formatting_functions(crudl_mock_model):
    """
    Este test comprueba que, para un modelo y PK dado, el método `show`:
    1. Obtiene ese objeto de la BD mediante el método de `peewee` `get`
    2. Formatea dicho objeto con el método `format_single_element`,
       usando como argumento el método `get_field_names()` del _meta del
       modelo.
    3. Imprime por pantalla el objeto formateado mediante el método
       `print_table`
    """

    from peewee2click import CRUDL

    format_func = 'peewee2click.CRUDL.format_single_element'
    print_func = 'peewee2click.CRUDL.print_table'
    model_mock = MagicMock()
    # Hacky!!! peewee usa el operador == de manera particular, así que devuelvo
    # ambos parámetros para asegurar que la invocación es exactamente así
    model_mock._meta.primary_key.__eq__ = lambda x, y: (x, y,)

    with patch(format_func) as format_mock, patch(print_func) as print_mock:
        CRUDL.show(model_mock, 3)

    model_mock.get.assert_called_once_with(model_mock._meta.primary_key == 3)
    format_mock.assert_called_once_with(
        model_mock.get.return_value,
        model_mock._meta.get_field_names.return_value)
    print_mock.assert_called_once_with(format_mock.return_value)


def test_update_method_returns_false_if_invalid_id(crudl_mock_model):
    """
    Este test comprueba que el método `update` devuelve False cuando se le pasa
    el pk de un objeto no existente
    """

    from peewee2click import CRUDL

    new_attrs = {'text_attr': 'foo'}
    assert CRUDL.update(crudl_mock_model, 1, True, **new_attrs) is False


def test_update_method_returns_true_if_valid_id(crudl_mock_model):
    """
    Este test comprueba que el método `update` devuelve True cuando se le pasa
    el pk de un objeto existente
    """

    from peewee2click import CRUDL

    new_attrs = {'text_attr': 'foo'}
    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    assert CRUDL.update(crudl_mock_model, 1, True, **new_attrs) is True


@pytest.mark.parametrize('force', [True, False])
def test_update_method_returns_false_if_no_changes(crudl_mock_model, force):
    """
    Este test comprueba que el método `update` devuelve False cuando se
    intenta actualizar un objeto sin pasarle parámetros a actualizar
    """

    from peewee2click import CRUDL

    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    assert CRUDL.update(crudl_mock_model, 1, force) is False


@pytest.mark.parametrize('force', [True, False])
def test_update_method_doesnt_call_update_if_no_changes(crudl_mock_model,
                                                        force):
    """
    Este test comprueba que el método `update` no llama a la función `update`
    de `peewee` si se intenta actualizar un objeto sin pasarle parámetros a
    actualizar
    """

    from peewee2click import CRUDL

    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    with patch.object(crudl_mock_model, 'update') as instance_update_mock:
        CRUDL.update(crudl_mock_model, 1, force)
        assert not instance_update_mock.called


@pytest.mark.parametrize('field,new_value', [
    ('text_attr', 'foo_text_attr'),
    ('char_attr', 'foo_char_attr'),
    ('int_attr', 32),
    ('bool_attr', False),
    ('float_attr', '32.0'),
    ('fk_attr', 1),
])
def test_update_method_updates_fields_in_database(crudl_mock_model, field,
                                                  new_value):
    """
    Este test comprueba que el método `update` actualiza los campos
    en base de datos después de una ejecución correcta
    """

    from peewee2click import CRUDL

    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    CRUDL.update(crudl_mock_model, 1, True, **{field: new_value})
    assert crudl_mock_model.select().where(
        getattr(crudl_mock_model, field) == new_value).exists()


def test_update_method_asks_for_confirmation_when_no_force():
    """
    Este test comprueba que el método `update` pregunta al usuario la
    confirmación usando el método `click.confirm` cuando el parámetro
    `force` es False
    """

    from peewee2click import CRUDL

    with patch('peewee2click.click.confirm') as click_mock:
        CRUDL.update(MagicMock(), 1, False)
    click_mock.assert_called_once()


def test_update_method_updates_object_when_confirm_is_true(crudl_mock_model):
    """
    Este test comprueba que el método `update` actualiza un objeto en base de
    datos cuando la respuesta a `click.confirm` es True
    """

    from peewee2click import CRUDL

    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    with patch('peewee2click.click.confirm', return_value=True):
        CRUDL.update(crudl_mock_model, 1, False, text_attr="new_mock")
    assert crudl_mock_model.select().where(
        crudl_mock_model.text_attr == "new_mock").exists()


def test_update_method_doesnt_update_object_when_confirm_is_false(
        crudl_mock_model):
    """
    Este test comprueba que el método `update` no actualiza un objeto en base
    de datos cuando la respuesta a `click.confirm` es False
    """

    from peewee2click import CRUDL

    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    with patch('peewee2click.click.confirm', return_value=False):
        CRUDL.update(crudl_mock_model, 1, False, text_attr="new_mock")
    assert not crudl_mock_model.select().where(
        crudl_mock_model.text_attr == "new_mock").exists()


def test_delete_method_delete_object_if_exists(crudl_mock_model):
    """
    Este test comprueba que el método `delete` elimina un objeto de base de
    datos cuando se le pasa el parámetro `force=True`
    """

    from peewee2click import CRUDL

    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    CRUDL.delete(crudl_mock_model, 1, force=True)
    assert not crudl_mock_model.select().where(
        crudl_mock_model.id == 1).exists()


def test_delete_method_asks_for_confirmation_when_no_force():
    """
    Este test comprueba que el método `delete` pregunta al usuario la
    confirmación usando el método `click.confirm` cuando el parámetro
    `force` es False
    """

    from peewee2click import CRUDL

    with patch('peewee2click.click.confirm') as click_mock:
        CRUDL.delete(MagicMock(), 1, False)
    click_mock.assert_called_once()


def test_delete_method_deletes_object_when_confirm_is_true(crudl_mock_model):
    """
    Este test comprueba que el método `delete` elimina un objeto de base de
    datos cuando la respuesta a `click.confirm` es True
    """

    from peewee2click import CRUDL

    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    with patch('peewee2click.click.confirm', return_value=True):
        CRUDL.delete(crudl_mock_model, 1, False)
    assert not crudl_mock_model.select().where(
        crudl_mock_model.id == 1).exists()


def test_delete_method_doesnt_delete_object_when_confirm_is_false(
        crudl_mock_model):
    """
    Este test comprueba que el método `delete` no elimina un objeto de base de
    datos cuando la respuesta a `click.confirm` es False
    """

    from peewee2click import CRUDL

    crudl_mock_model.create(text_attr="mock", char_attr="", int_attr=1,
                            bool_attr=True)
    with patch('peewee2click.click.confirm', return_value=False):
        CRUDL.delete(crudl_mock_model, 1, False)
    assert crudl_mock_model.select().where(crudl_mock_model.id == 1).exists()


def test_list_method_selects_all_objects_and_print_them():
    """
    Este test comprueba que el método `list` para un modelo y unos campos
    dados:
    1. Obtiene de BD todos los objetos de ese tipo con el método `select` de
       peewee
    2. Formatea dichos objetos con el método `format_multiple_elements`,
       usando como argumento el parámetro fields dado
    3. Imprime por pantalla el objeto formateado mediante el método
       `print_table` pasando como parámetro headers los fields dados
    """

    from peewee2click import CRUDL

    format_func = 'peewee2click.CRUDL.format_multiple_elements'
    print_func = 'peewee2click.CRUDL.print_table'
    model_mock = MagicMock()
    fields = [MagicMock()]

    with patch(format_func) as format_mock, patch(print_func) as print_mock:
        CRUDL.list(model_mock, fields)

    model_mock.select.assert_called_once()
    format_mock.assert_called_once_with(model_mock.select.return_value, fields)
    print_mock.assert_called_once_with(format_mock.return_value,
                                       headers=fields)


def test_list_method_adds_extra_fields():
    """
    Este test comprueba que el método `list` para un modelo, unos campos base
    y unos campos extra dados:
    1. Obtiene de BD todos los objetos de ese tipo con el método `select` de
       peewee
    2. Formatea dichos objetos con el método `format_multiple_elements`,
       usando como argumentos los campos base y los extra
    3. Imprime por pantalla el objeto formateado mediante el método
       `print_table` pasando como parámetro headers los campos base y los extra
    """

    from peewee2click import CRUDL

    format_func = 'peewee2click.CRUDL.format_multiple_elements'
    print_func = 'peewee2click.CRUDL.print_table'
    model_mock = MagicMock()
    base_fields = [MagicMock()]
    extra_fields = [MagicMock()]

    with patch(format_func) as format_mock, patch(print_func) as print_mock:
        CRUDL.list(model_mock, base_fields, extra_fields=extra_fields)

    model_mock.select.assert_called_once()
    format_mock.assert_called_once_with(model_mock.select.return_value,
                                        base_fields + extra_fields)
    print_mock.assert_called_once_with(format_mock.return_value,
                                       headers=base_fields + extra_fields)


def test_list_method_removes_duplicated_fields():
    """
    Este test comprueba que el método `list` para un modelo, unos campos base
    y unos campos extra dados (ambos con elementos repetidos):
    1. Obtiene de BD todos los objetos de ese tipo con el método `select` de
       peewee
    2. Formatea dichos objetos con el método `format_multiple_elements`,
       usando como argumentos los campos base y los extra, pero con los
       elementos sin repetir en ambos casos
    3. Imprime por pantalla el objeto formateado mediante el método
       `print_table` pasando como parámetro headers los campos base y los
       extra, pero con los elementos sin repetir en ambos casos
    """

    from peewee2click import CRUDL

    format_func = 'peewee2click.CRUDL.format_multiple_elements'
    print_func = 'peewee2click.CRUDL.print_table'
    model_mock = MagicMock()
    field_mock = MagicMock()
    extra_field_mock = MagicMock()
    # Fields repetidos, comprobaremos que se limitan a dos (en lugar de cuatro)
    base_fields = [field_mock, field_mock]
    extra_fields = [extra_field_mock, extra_field_mock]

    with patch(format_func) as format_mock, patch(print_func) as print_mock:
        CRUDL.list(model_mock, base_fields, extra_fields=extra_fields)

    # En los asserts comparamos contra una lista que solo tiene dos fields
    expected_fields = [field_mock, extra_field_mock]

    model_mock.select.assert_called_once()
    format_mock.assert_called_once_with(model_mock.select.return_value,
                                        expected_fields)
    print_mock.assert_called_once_with(format_mock.return_value,
                                       headers=expected_fields)


def test_number_of_arguments_in_list_count_matching_strings():
    """
    Este test comprueba que el método `_number_of_arguments_in_list` devuelve
    el número de keys de un diccionario coincidentes con los argumentos dados
    """

    from peewee2click import _number_of_arguments_in_list

    ctx = {'foo': 'foo', 'bar': 'bar', 'baz': 'baz'}
    assert _number_of_arguments_in_list(ctx, 'foo', 'bar') == 2


def test_number_of_arguments_in_list_doesnt_count_None_values():
    """
    Este test comprueba que el método `_number_of_arguments_in_list`
    ignora las keys del diccionario que tengan como valor `None`
    """

    from peewee2click import _number_of_arguments_in_list

    ctx = {'foo': 'foo', 'bar': None, 'baz': 'baz'}
    assert _number_of_arguments_in_list(ctx, 'foo', 'bar') == 1


def test_one_and_only_one_raises_UsageError_when_both_params():
    """
    Este test comprueba que el método `_one_and_only_one`
    eleva `click.UsageError` en caso de encontrarse en el diccionario
    ctx más de uno de los parámetros dados
    """

    from peewee2click import one_and_only_one

    ctx = {'foo': 'foo', 'bar': 'bar'}
    with pytest.raises(click.UsageError):
        one_and_only_one(ctx, 'foo', 'bar')


def test_one_and_only_one_raises_UsageError_when_no_params():
    """
    Este test comprueba que el método `_one_and_only_one`
    eleva `click.UsageError` en caso de no encontrarse en el diccionario
    ctx ninguno de los parámetros dados
    """

    from peewee2click import one_and_only_one

    ctx = {'not_present': 'not_present'}
    with pytest.raises(click.UsageError):
        one_and_only_one(ctx, 'foo', 'bar')


def test_max_one_raises_UsageError_when_more_than_one_param():
    """
    Este test comprueba que el método `max_one` eleva `click.UsageError`
    en caso de encontrarse en el diccionario ctx más de uno de los parámetros
    dados
    """

    from peewee2click import max_one

    ctx = {'foo': 'foo', 'bar': 'bar'}
    with pytest.raises(click.UsageError):
        max_one(ctx, 'foo', 'bar')

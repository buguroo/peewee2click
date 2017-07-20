import collections
import datetime
import functools
import itertools
import warnings

from tabulate import tabulate
import click


class DateParamType(click.ParamType):
    name = 'date'

    def convert(self, value, param, ctx):
        try:
            # date will fail if it doesn't get exactly three params
            result = datetime.date(*[int(x) for x in value.split('-')])
        except (ValueError, TypeError):
            self.fail("{} is not a date in the form YYYY-MM-DD".format(value))
        else:
            return result


DATE_PARAM_TYPE = DateParamType()


def _number_of_arguments_in_list(ctx, *what):
    """
    Return the number of `what` found as `ctx` dict keys with a value
    other than `None`.

    :param ctx: Arguments to check.
    :type ctx: dict

    :param what: List of arguments corresponding to `ctx` keys.
    :type what: list

    """
    return sum(1 for w in what if ctx.get(w) is not None)


def one_and_only_one(ctx, *what):
    """
    Check the non-repetition of arguments.

    :param ctx: Arguments to check.
    :type ctx: dict

    :param what: List of arguments that must appear only once.
    :type what: list

    """

    if _number_of_arguments_in_list(ctx, *what) != 1:
        raise click.UsageError(
            ("One and only one of these parameters can be provided "
             "at a time: %r") % [what])


def max_one(ctx, *what):
    """
    Implements a method like `mutually_exclusive_group`

    :param ctx: Arguments to check.
    :type ctx: dict

    :param what: List of arguments that are mutually exclusive.
    :type what: list

    """

    if _number_of_arguments_in_list(ctx, *what) > 1:
        raise click.UsageError(
            ("At most one of these parameters can be provided "
             "at a time: %r") % [what])


class CRUDL:
    """
    CRUD+L over peewee models.

    """
    TABLEFMT = "plain"

    @classmethod
    def print_table(cls, *args, **kwargs):
        table = tabulate(*args, tablefmt=cls.TABLEFMT, **kwargs)
        click.echo("\n{}\n".format(table))

    @staticmethod
    def format_single_element(elem, fields):
        return [(k, repr(getattr(elem, k))) for k in fields]

    @staticmethod
    def format_multiple_elements(elems, fields):
        res = []
        for e in elems:
            res.append([repr(getattr(e, f)) for f in fields])
        return res

    @staticmethod
    def click_options_from_model_fields(model, skip=None):
        def _options_from_model():
            DBFIELD_TO_TYPE = {
                ("int",
                 "int unsigned"): int,
                ("bool", ): bool,
                ("text", "string"): str,
                ("float", ): float,
                ("date", ): DATE_PARAM_TYPE,
                ("primary_key", ): None
            }

            fields = sorted(model._meta.fields.values(), reverse=True)
            for field in fields:
                if skip and field.name in skip:
                    continue

                for db_fields, asc_type in DBFIELD_TO_TYPE.items():
                    if field.get_db_field() in db_fields:
                        type_ = asc_type
                        break
                else:
                    warnings.warn(
                        ("Unknown database type `{field.db_field}` option "
                         "`{model._meta.name}.{field.name}` can't be "
                         "rendered.").format(model=model, field=field),
                        SyntaxWarning)
                    type_ = str

                if type_ is None:
                    # This type of field doesn't map to an argument
                    continue

                if field.help_text is None:
                    help = "No help. Please, document the model."
                else:
                    help = field.help_text

                name = '--' + field.name.replace('_', '-')
                if field.null:
                    yield click.option(
                        name + "-set-null",
                        is_flag=True,
                        help="Set {} to NULL.".format(field.name))

                yield click.option(name,
                                   type=type_,
                                   help=help)

        # Using function composition we compose all the decorators generated by
        # `_options_from_model` and we return one that groups them all.
        return lambda f: functools.reduce(lambda g, h: h(g),
                                          _options_from_model(),
                                          f)

    @staticmethod
    def fields_from_options(options):
        null_fields = {k[:-len('_set_null')]: None
                       for k, v in options.items()
                       if k.endswith('_set_null') and v}

        non_null_fields = {k: v for k, v in options.items()
                           if not k.endswith('_set_null') and v is not None}

        return collections.ChainMap(null_fields, non_null_fields)

    @classmethod
    def create(cls, model, force, **options):
        """
        C: CREATE

        """
        fields = cls.fields_from_options(options)
        obj = model(**fields)

        def _create():
            # Force insert to prevent peewee trying to do the update in case of
            # non auto-incremental ID.
            obj.save(force_insert=True)
            click.echo("The following entry was created:")
            cls.show(model, obj.get_id())
            return True

        if force:
            return _create()
        else:
            click.echo("You are about to create the following entry:")

            fields = sorted(model._meta.fields.keys())
            try:
                preview = cls.format_single_element(obj, fields)
                cls.print_table(preview)
            except Exception as exc:
                click.echo("Malformed entry: %s" % exc.__class__.__name__)
                return False

            if click.confirm("Are you sure?"):
                return _create()

    @classmethod
    def show(cls, model, pk):
        """
        R: READ

        """
        fields = sorted(model._meta.fields.keys())
        try:
            # We get the key through meta, as it could be a compose key
            obj = model.get(model._meta.primary_key == pk)
        except model.DoesNotExist:
            click.echo("Registry {} does not exists.".format(pk))
            return False
        else:
            data = cls.format_single_element(obj, fields)
            cls.print_table(data)
            return True

    @classmethod
    def update(cls, model, pk, force, **options):
        """
        U: UPDATE

        """
        changes = cls.fields_from_options(options)

        if not changes:
            click.echo("Nothing to change.")
            return False

        def _update():
            # We get the key through meta, as it could be a compose key
            records = (model.update(**changes)
                            .where(model._meta.primary_key == pk)
                            .execute())

            click.echo("Changed {} records.".format(records))
            cls.show(model, pk)
            return records > 0

        if force:
            return _update()
        else:
            click.echo("You are about to update the following record:")
            cls.show(model, pk)
            click.echo("With the following information:")
            cls.print_table([[k, v] for k, v in changes.items()])
            if click.confirm("Are you sure?"):
                return _update()

    @classmethod
    def delete(cls, model, pk, force):
        """
        D: DELETE

        """
        def _delete():
            try:
                # We get the key through meta, as it could be a compose key
                obj = model.get(model._meta.primary_key == pk)
            except model.DoesNotExist:
                click.echo("Registry {} does not exists.".format(pk))
            else:
                obj.delete_instance(recursive=True, delete_nullable=True)
                click.echo("Registry {} removed.".format(pk))
                return True

        if force:
            return _delete()
        else:
            click.echo("You are about to remove the following record:")
            if cls.show(model, pk) and click.confirm("Are you sure?"):
                return _delete()
            else:
                return False

    @classmethod
    def list(cls, model, base_fields, extra_fields=None):
        """
        L: LIST

        """
        # We concatenate base fields with extra_fields, removing duplicates
        # and keeping the order.
        fields = list(base_fields)
        if extra_fields is not None:
            fields += list(extra_fields)
        fields = [f for f, _ in itertools.groupby(fields)]

        objs = model.select()
        data = cls.format_multiple_elements(objs, fields)
        cls.print_table(data, headers=fields)
        return True

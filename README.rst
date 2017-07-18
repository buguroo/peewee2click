peewee2click: Easy command-line interfaces for Peewee models
============================================================

peewee2click is an easy to use Click_ helper to create command-line CRUDL interfaces
for your peewee_ models.

What are command-line CRUDL interfaces?
---------------------------------------

Interfaces that let you **Create**, **Read**, **Update**, **Delete** or
**List** your models via command-line.

Installation
------------

Just run ``pip install peewee2click``.

Example of use
--------------

Let supose you have the following *peewee* class:

.. code-block:: python

    import peewee

    class MyClass(peewee.Model):
        my_char_field = peewee.CharField(
            max_length=8, help_text="Field to store char.")
        my_int_field = peewee.IntegerField(
            default=5, help_text="Field to store int.")

To create a very basic command-line CRUDL you only need the following code:

.. code-block:: python

    from peewee2click import CRUDL
    import click

    @click.command(help="Creates a new myclass")
    @CRUDL.click_options_from_model_fields(MyClass)
    def create(**fields):
        CRUDL.create(MyClass, **fields)

    @click.command(help="Shows myclass information")
    @click.argument("primary_key", type=int)
    def show(primary_key):
        CRUDL.show(MyClass, primary_key)

    @click.command(help="Updates myclass information")
    @click.argument("primary_key") 
    @CRUDL.click_options_from_model_fields(MyClass)
    def update(primary_key, **changed_fields):
        CRUDL.update(MyClass, primary_key, **changed_fields)

    @click.command(help="Deletes an existing myclass")
    @click.argument("primary_key")
    def delete(primary_key):
        CRUDL.delete(MyClass, primary_key)

    @click.command("list", help="Enumerate myclasses")
    @click.option("fields", "--add-field", multiple=True,
                  help="Shows a custom field in the result")
    def list_(fields):
        base_fields = ('id', 'my_char_field', 'my_int_field')

        CRUDL.list(MyClass, base_fields, extra_fields=fields)

As you can see, ``CRUDL.click_options_from_model_fields`` gathers all the
Model fields for you, creating automatically the parameters options
"``--my-char-field=<new_value>``" and "``-my-int-field=<new_value>``" for the
`create` and `update` commands.


Other commands
--------------

Besides the ``CRUDL`` methods seen in the example above, CRUDL also implements
two helper functions: ``one_and_only_one`` and ``max_one``. Both provides a way
of checking that arguments are passed in a proper way.

Check the docstrings of the functions for further information.

Running the tests
-----------------

Install the develop dependencies: ``pip install -e requirements/develop.txt``. Then run ``tox``.

You will need `sqlite` support in your Python client to run the tests.


.. _peewee: http://docs.peewee-orm.com/en/latest/
.. _Click: http://click.pocoo.org/5/

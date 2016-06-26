Schemagic / Schemagic.web:  [some kind of tagline!]
===================================================

.. image:: https://img.shields.io/badge/pypi-v0.7.0-green.svg
    :target: https://pypi.python.org/pypi/schemagic

Schemagic is a rather utilitarian re-imagining of the wonderful and powerful clojure library `Schema <https://github.com/plumatic/schema>`_!
Schemagic.web is what programmers do when they hate web programming, but want to make their programs accessible to the web.


Installation
------------

It's a wheel on Pypi, and it's 2 and 3 compatible.
To install Schemagic, simply:

.. code-block:: bash

    $ pip install schemagic


How to Contribute
-----------------

#. What the codebase needs primarily is a large suite of validation functions, such as those found in validators.py
#. Additional support for Schemagic.web would also be welcome.  Currently it only supports Flask.
#. Fork `the repository`_ on GitHub to start making your changes to the **master** branch (or branch off of it).
#. Send a pull request and email `the maintainer`_.  Do me a favor and tag your subject with [Schemagic] :)

.. _`the repository`: https://github.com/TJTolton/schemagic
.. _`the maintainer`: tjtolton@gmail.com


Documentation
-------------

For now, I'm simply going to put all the documentation here in the README.

But enough talk.  Lets build a schema and start using it.

.. code-block:: python

    >>> import schemagic
    >>> list_of_ints = [int]
    >>> schemagic.validate_against_schema(list_of_ints, [1, 2, 3])
    [1, 2, 3]
    >>> schemagic.validate_against_schema(list_of_ints, ["hello", "my friends"])
    Traceback (most recent call last):
      ...
    ValueError: invalid literal for int() with base 10: 'hello'

The error you see here (customizeable) is the error you get when you try to call:

.. code-block:: python

    >>> int("hello")
    Traceback (most recent call last):
      ...
    ValueError: invalid literal for int() with base 10: 'hello'

And it occurred because list_of_ints specified that the function to check every member of the list against was int()


Basic Schemagic Usage
---------------------

Schema checking is quite flexible, and all checks are done recursively.  Lets go through some more examples:

**Map Template**:
*if you only provide a schema with one (callable) key and one value*

.. code-block:: python

    >>> string_to_int_map = {str:int}
    >>> schemagic.validate_against_schema(string_to_int_map, {"hello": 5, "friends": 6})
    {'friends': 6, 'hello': 5}

**Map with Specific Keys**
*if you provide  a schema with strings as keys*

.. code-block:: python

    >>> string_to_int_map = {str:int}
    >>> schemagic.validate_against_schema(string_to_int_map, {"hello": 5, "friends": 6})
    {'friends': 6, 'hello': 5}

**Sequence Template**:
*if you provide a sequence containing only one item as a schema*

.. code-block:: python

    >>> list_of_ints = [int]
    >>> schemagic.validate_against_schema(string_to_int_map, [1, 2, 3, 4])
    [1, 2, 3, 4]

**Strict Sequence**:
*if you provide a sequence with multiple items as a schema*

.. code-block:: python

    >>> list_with_3_items_int_str_and_intstrmap = [int, str, {int: str}]
    >>> schemagic.validate_against_schema(string_to_int_map, [1, "hello", {5: "friends", 12: "and", 90: "world"}])
    [1, "hello", {5: "friends", 12: "and", 90: "world"}]

**Validation Function**:
*if you provide a function as a schema*

.. code-block:: python

    >>> def null(data):
    ...    if data is not None:
    ...        raise TypeError("expected Nonetype, got {0}".format(data))
    >>> schemagic.validate_against_schema(null, None)
    >>> schemagic.validate_against_schema(null, "hello!")
    Traceback (most recent call last):
      ...
    TypeError: expected Nonetype, got hello


**Compose Schema Definitions Recursively Ad Nauseam**:
*this is where the real value lies*

.. code-block:: python

    >>> def enum(*possible_values):
    ...     def _validator(data):
    ...        if not data in possible_values:
    ...            raise ValueError()
    ...        return data
    ...     return _validator
    >>> event = {
    ...    "event_type": enum("PRODUCTION", "DEVELOPMENT")
    ...    "event_name": str,
    ...}
    >>> dispatch_request = {
    ...    "events": [event],
    ...    "requested_by": str
    ...}
    >>> schemagic.validate_against_schema(dispatch_request,
    ...     {"events": [{"event_type": "DEVELOPMENT",
    ...                  "event_name": "demo_business_process"},
    ...                 {"event_type": "DEVELOPMENT",
    ...                  "event_name": "demo_other_business_process"}],
    ...      "requested_by": "Tyler Tolton"})
    {"events": [{"event_type": "DEVELOPMENT", "event_name": "demo_business_process"}, {"event_type": "DEVELOPMENT", "event_name": "demo_other_business_process"}], "requested_by": "Tyler Tolton"}


Schemagic.validator Usage
-------------------------

**Use the Schemagic.validator for increased message clarity and control**:
*implemented using the "Function Validator"*

.. code-block:: python

    >>> list_of_ints_validator = schemagic.validator([int], "Business Type: list of integers")
    >>> list_of_ints_validator([1, "not an int", 3])
    Traceback (most recent call last):
      ...
    ValueError: Bad value provided for Business Type: list of integers. - error: ValueError: invalid literal for int() with base 10: 'not an int' schema: [<type 'int'>] value: [1, 'not an int', 3]

**Supply predicate to prevent/enable validation conditionally**:

.. code-block:: python

    >>> __env__ = None
    >>> WHEN_IN_DEV_ENV = lambda: __env__ == "DEV"
    >>> validate_in_dev = partial(schemagic.validator, validation_predicate=WHEN_IN_DEV)
    >>> list_of_ints_validator = validate_in_dev([int], "integer list")
    >>> __env__ = "DEV"
    >>> list_of_ints_validator([1, "not an int", 3])
    Traceback (most recent call last):
      ...
    ValueError: Bad value provided for integer list. - error: ValueError: invalid literal for int() with base 10: 'not an int' schema: [<type 'int'>] value: [1, 'not an int', 3]
    >>> __env__ = "PROD"
    >>> list_of_ints_validator([1, "not an int", 3])
    [1, "not an int", 3]


**Coerce data as it is validated**:
*note: validate against schema*

.. code-block:: python

    >>> validate_and_coerce = partial(schemagic.validator, coerce_data=True)
    >>> list_of_ints_validator_and_coercer = validate_and_coerce([int], "integer list")
    >>> list_of_ints_validator_only = schemagic.validator([int], "integer_list")
    >>> list_of_ints_validator_only(["1", "2", "3"])
    ["1", "2", "3"]
    >>> # Note that the if you pass an integer string to int() it returns an integer.
    >>> # this makes it s dual purpose validator and coercer.
    >>> list_of_ints_validator_and_coercer(["1", "2", "3"])
    [1, 2, 3]


Schemagic.web
-------------

Schemagic.web is where rubber meets the road in practical usage.  It provides an easy way to communicate between
services, between developers, and between development teams in an agile environment.  The webservice business world was
the furnace in which schemagic was forged.  Get ready to outsource yourself.

To demo the schemagic.web workflow, lets assume the roles of the first people in the world to discover a way
to (gasp) compute the fibonacci sequence in python.

*note: this code is all pulled from Peter Norvig's excellent* `Design of Computer Programs  <https://www.udacity.com/course/design-of-computer-programs--cs212>`_ *Udacity class.*

.. code-block:: python

    def memo(fn):
        _cache = {}
        def _f(*args):
            try:
                return _cache[args]
            except KeyError:
                _cache[args] = result = fn(*args)
                return result
            except TypeError:
                return fn(*args)
        _f.cache = _cache
        return _f

    @memo
    def fib(n):
        if n == 0 or n == 1:
            return 1
        else:
            return fib(n - 1) + fib(n - 2)

    >>> fib(30)
    1346269

Brilliant!  Well, now we'll of course want to share this discovery with the world in the form of a microservice, so that
others need not know the inner workings of this complex and dangerous algorithm.

Lets walk through how we might set up this webservice in flask:

.. code-block:: python

    from flask import Flask, json

    app = Flask(__name__)

    def memo(fn):
        _cache = {}
        def _f(*args):
            try:
                return _cache[args]
            except KeyError:
                _cache[args] = result = fn(*args)
                return result
            except TypeError:
                return fn(*args)
        _f.cache = _cache
        return _f

    @memo
    def fib(n):
        if n == 0 or n == 1:
            return 1
        else:
            return fib(n - 1) + fib(n - 2)

    @app.route("/fibonacci/<index>")
    def web_fib_endpoint(index):
        try:
            index = int(index)
        except ValueError:
            return Response(
                status=400,
                response="Argument to /fibonacci/ must be an integer"
            )
        return Response(
            status=200,
            response=json.dumps(fib(index))
        )


    if __name__ == '__main__':
        app.run(port=5000)


While this pattern is certainly serviceable, it is rather heavyweight to simply expose a function to the web.
Additionally, the code doesn't lend itself well to easily documenting its input and output.
Lets see an adapted version of this code using schemagic.web utilities.

.. code-block:: python

    from flask.app import Flask
    from schemagic.web import service_registry

    app = Flask(__name__)
    register_fibonnacci_services = service_registry(app)


    def memo(fn):
        _cache = {}
        def _f(*args):
            try:
                return _cache[args]
            except KeyError:
                _cache[args] = result = fn(*args)
                return result
            except TypeError:
                return fn(*args)
        _f.cache = _cache
        return _f

    @memo
    def fib(n):
        if n == 0 or n == 1:
            return 1
        else:
            return fib(n - 1) + fib(n - 2)

    register_fibonnacci_services(
        dict(rule="/fibonacci",
             input_schema={"n" : int},
             output_schema=int,
             fn=fib))

    if __name__ == '__main__':
        app.run(port=5000)

There, now we simply *describe* our service with data.
What is the service endpoint, what is the input, what is the output,
and what is the implementation that delivers the contract defined herein.

Important notes:

#. The webservices all uniformally use POST requests to transmit data.  The data supplied to the endpoints comes from the payload of the request.
#. Regarding the above example, there are alternate ways of describing the input to fib().  We could have said "input_schema=int", which would imply that the POST request payload should be an int, unwrapped.
    the notation used in the example requires the POST request to provide its data via keyword.


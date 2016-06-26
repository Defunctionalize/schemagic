import re
from functools import partial, update_wrapper

from schemagic.core import validate_against_schema
from schemagic.utils import merge


def predicate_validator(predicate, name=None, coercer=None, message=None, data=None):
    """Builds new validator function that tests, and optionally coerces, data against the supplied predicate and coercer

    :param predicate: function that accepts one argument, the data, returns true if data is good, false otherwise.
    :param name: name of the supplied predicate.  useful when building validators from anonymous functions.
    :param coercer: a function that accepts the data and returns a modification of that data.  If no coercer is provided,
        the data will still be subject to any coercions that occur within the validation.  This is to allow for additional
        flexibility, for instance, you may want to convert a datetime string into a datatime object before validating it.
    :param message: A message that described the problem with the data if it wasn't validated correctly.
        This message will be automatically suffixed with a printout of the data recieved by the validator.
        If message is not provided, a default message is used that references the predicate by name.
    :param data: the data to be validated
    :return: if data is not supplied, returns a copy of the predicate validator function with all the other
            values "filled in".  i.e. it returns a curried function.
        If the data is supplied, returns the, possibly transformed, data if it is valid, else throws an error.
    """
    predicate.__name__ = name or predicate.__name__
    if data is None:
        return update_wrapper(partial(predicate_validator, predicate, name, coercer, message), predicate)
    data = coercer(data) if coercer else data
    message = (message or "data did not meet requirements of the predicate {0}".format(predicate.__name__)) + "\n value: {0}".format(data)
    if not predicate(data):
        raise ValueError(message)
    return data

formatted_string = lambda str_format, **kwargs: predicate_validator(
    lambda data: re.match(str_format, data),
    **merge(dict(name="formatted_string: {0}".format(str_format),
                 coercer=str,
                 message="string not of expected format: expected: {0}".format(format)),
            kwargs))
"""Stringifies the data, then matches it against the supplied regex string.  Valid if match is returned"""

#: ``formatted_string(r'\d+\-\d+\-\d+')``: checks to see if the data is of the type returned by stringifying a datetime.date object
date_string = formatted_string(r'\d+\-\d+\-\d+')

#: ``formatted_string(r'\d+\-\d+\-\d+ \d+:\d+:\d+\.\d+')``: checks to see if the data is of the type returned by stringifying a datetime.datetime object
datetime_string = formatted_string(r'\d+\-\d+\-\d+ \d+:\d+:\d+\.\d+')

#: ``predicate_validator``: Usually composed with or_, checks to see if the data is the value None
null = predicate_validator(lambda val: val is None, name="null")

or_ = lambda *schemata: predicate_validator(
    lambda val: any(validate_against_schema(schema, val) for schema in schemata),
    name="any of schema's {0}".format(schemata),
)
"""checks to see if the data is valid with any of the given data definitions"""


enum = lambda *possible_vals: predicate_validator(
    lambda val: val in possible_vals,
    name="enumeration of allowable values: {0}".format(possible_vals),
)
"""checks to see if the data is one of the provided values"""

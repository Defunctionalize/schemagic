import re
from functools import partial, update_wrapper

from schemagic.core import validate_against_schema
from schemagic.utils import merge


def predicate_validator(predicate, name=None, coercer=None, message=None, data=None):
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

date_string = formatted_string(r'\d+\-\d+\-\d+')
datetime_string = formatted_string(r'\d+\-\d+\-\d+ \d+:\d+:\d+\.\d+')


null = predicate_validator(lambda val: val is None, name="null")
or_ = lambda *schemata: predicate_validator(
    lambda val: any(validate_against_schema(schema, val) for schema in schemata),
    name="any of schema's {0}".format(schemata),
)
enum = lambda *possible_vals: predicate_validator(
    lambda val: val in possible_vals,
    name="enumeration of allowable values: {0}".format(possible_vals),
)

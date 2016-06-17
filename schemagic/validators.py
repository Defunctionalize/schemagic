import re
from functools import partial

def predicate_validator(predicate, coercer=None, message=None, data=None):
    if data is None:
        return partial(predicate_validator, predicate, coercer, message)
    data = coercer(data) if coercer else data
    message = message or "data did not meet requirements of the predicate {0}.  recieved: {1}".format(predicate, data)
    if not predicate(data):
        raise ValueError(message)
    return data

def formatted_string(format, data=None):
    if data is None:
        return partial(formatted_string, format)
    return predicate_validator(
        predicate=lambda data: re.match(format, data),
        coercer=str,
        message="string not of expected format: expected: {0}, got: {1}".format(format, data),
        data=data
    )

date_string = formatted_string(r'\d+\-\d+\-\d+')
datetime_string = formatted_string(r'\d+\-\d+\-\d+ \d+:\d+:\d+\.\d+')


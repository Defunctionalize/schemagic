import re
from functools import partial


def formatted_string(format, data=None):
    if data is None:
        return partial(formatted_string, format)
    stringified = "{0}".format(data)

    if not re.match(format, stringified):
        raise ValueError("string not of expected format: expected: {0}, got: {1}".format(format, stringified))

    return stringified

date_string = formatted_string(r'\d+\-\d+\-\d+')
datetime_string = formatted_string(r'\d+\-\d+\-\d+ \d+:\d+:\d+\.\d+')


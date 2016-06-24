import collections
from functools import partial

from schemagic.utils import merge_with, multiple_dispatch_fn

WHEN_DEBUGGING = lambda: __debug__

def validate_map_template(schema, value):
    """Ensures all the keys and values of the given data are valid with the schema's key and value validators

    :param schema: A map template, i.e. a dict with one item, and the key is not a string, e.g. {int: str}
    :param value: Any data which will be checked to make sure it matches the prescribed pattern
    :return: The data after it has been run through its validators.
    """
    key_schema, value_schema = schema.items()[0]
    validate_key_val_pair = lambda key, val: (validate_against_schema(key_schema, key), validate_against_schema(value_schema, val))
    return dict(map(validate_key_val_pair, value.keys(), value.values()))

def validate_keyed_mapping(schema, value):
    """Ensures all required keys are present, and that their corresponding value matches with the schema's prescription

    :param schema: A map of strings to data definitions, e.g. {"name": str, "age": int}
    :param value: Any data which will be checked to make sure it matches the prescribed pattern
    :return: The data after it has been run through its validators.
    """
    missing_keys = set(schema.keys()) - set(value.keys())
    if missing_keys:
        raise ValueError("Missing keys {0} for value {1}".format(missing_keys, value))
    return merge_with(validate_against_schema, schema, value)

def validate_sequence_template(schema, value):
    """Ensures each item of the value is of the patterns specified by the schema['s first element].

    :param schema: A sequence of one element, and that element is a data definition, e.g. [int] or [{str: int}]
    :param value: Any data which will be checked to make sure it matches the prescribed pattern
    :return: The data after it has been run through its validators.
    """
    return map(schema[0], value)

def validate_strict_sequence(schema, value):
    """Ensures that the elements of the value are in the same order and valid with the same definitions in the schema.

    :param schema: A sequence of data definitions, e.g. [int, {str:int}, [str, int, int], {"age": int}]
    :param value: Any data which will be checked to make sure it matches the prescribed pattern
    :return: The data after it has been run through its validators.
    """
    if not len(schema) == len(value):
        raise ValueError("sequence has a different number of elements than its schema prescribes.  value: {0}, schema: {1}".format(value, schema))
    return map(lambda sub_schema, sub_value: validate_against_schema(sub_schema, sub_value), schema, value)

is_map_template = lambda schema: isinstance(schema, collections.MutableMapping) and len(schema.items()) is 1 and not isinstance(schema.keys()[0], str)
is_keyed_mapping = lambda schema: isinstance(schema, collections.MutableMapping) and not is_map_template(schema)
is_sequence_template = lambda schema: isinstance(schema, collections.Sequence) and len(schema) is 1
is_strict_sequence = lambda schema: isinstance(schema, collections.Sequence) and 1 < len(schema)

validate_against_schema = multiple_dispatch_fn({
    lambda schema, value: is_sequence_template(schema): validate_sequence_template,
    lambda schema, value: is_strict_sequence(schema): validate_strict_sequence,
    lambda schema, value: is_map_template(schema): validate_map_template,
    lambda schema, value: is_keyed_mapping(schema): validate_keyed_mapping},
    default=lambda schema, value: schema(value))
validate_against_schema.__name__ = "validate_against_schema"
validate_against_schema.__doc__ = \
    """Ensures that the data is valid with the given schema

    :param schema: A data definition.  This definition can take any of 5 forms --
    #. **function**: the function will be called fn(data) and expected to return the data, if correct, or throw an error
    #. **map template**:  a dict with one item, where both the key and value are data definitions, e.g. {int: [str]}
    #. **keyed mapping**: A map of strings to data definitions, e.g. {"name": str, "age": int}
    #. **sequence template**: A one element sequence, where the element is a data definition, e.g. [int] or [{str: int}]
    #. **strict sequence**: A sequence of data definitions, e.g. [int, {str:int}, [str, int, int], {"age": int}]

    Notable things that do **not** count as data definitions include primitive data such as strings, integers, or bools.
    These data could be used as components of data definition, but should not be used alone in places that expect
    data definitions.  For instance ["hello"] is not a valid sequence template, because the element in it is not a data
    definition.

    I suppose you could also compose custom classes into your data definitions if you wanted.  you heathen. ;)

    :param value: Any data which will be checked to make sure it matches the prescribed pattern
    :return: The data after it has been run through its validators.
    """


def validator(schema, subject_name_str, validation_predicate=None, coerce_data=False, data=None):
    if data is None:
        return partial(validator, schema, subject_name_str, validation_predicate, coerce_data)
    validation_predicate = validation_predicate or WHEN_DEBUGGING
    if not validation_predicate():
        return data
    try:
        coerced_and_validated_data = validate_against_schema(schema, data)
        return coerced_and_validated_data if coerce_data else data
    except Exception as e:
        message_details = {
            "subject": subject_name_str,
            "error": "{0}: {1}".format(e.__class__.__name__, e),
            "value": data,
            "schema": schema
        }
        raise ValueError("Bad value provided for {subject}. - error: {error} schema: {schema} value: {value}".format(**message_details))
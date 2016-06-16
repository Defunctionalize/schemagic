import collections
from functools import partial, wraps

from schemagic.validators import date_string
from utils import merge_with, multiple_dispatch_fn

ALWAYS = lambda: True
WHEN_DEBUGGING = lambda: __debug__
IDENTITY = lambda x: x

def validate_map_template(schema, value):
    key_schema, value_schema = schema.items()[0]
    validate_key_val_pair = lambda key, val: (validate_against_schema(key_schema, key), validate_against_schema(value_schema, val))
    return dict(map(validate_key_val_pair, value.keys(), value.values()))

def validate_keyed_mapping(schema, value):
    missing_keys = set(schema.keys()) - set(value.key())
    if missing_keys:
        raise ValueError("Missing keys {0} for value {1}".format(missing_keys, value))
    return merge_with(validate_against_schema, schema, value)

def validate_sequence_template(schema, value):
    return map(schema[0], value)

def validate_strict_sequence(schema, value):
    if not len(schema) == len(value):
        raise ValueError("sequence has a different number of elements than its schema prescribes.  value: {0}, schema: {1}".format(value, schema))
    return map(lambda sub_schema, sub_value: validate_against_schema(sub_schema, sub_value), schema, value)

is_map_template = lambda schema: isinstance(schema, collections.MutableMapping) and len(schema.items()) is 1 and not isinstance(schema.keys()[0], str)
is_keyed_mapping = lambda schema: isinstance(schema, collections.MutableMapping) and not is_map_template(schema)
is_sequence_template = lambda schema: isinstance(schema, collections.Sequence) and len(schema) is 1
is_strict_sequence = lambda schema: isinstance(schema, collections.Sequence) and 1 < len(schema)

validate_against_schema = multiple_dispatch_fn( "validate_against_schema", {
    lambda schema, value: is_sequence_template(schema): validate_sequence_template,
    lambda schema, value: is_strict_sequence(schema): validate_strict_sequence,
    lambda schema, value: is_map_template(schema): validate_map_template,
    lambda schema, value: is_keyed_mapping(schema): validate_keyed_mapping},
    default=lambda schema, value: schema(value))

def validator(schema, message, coerce_data=True, data=None):
    if data is None:
        return partial(validator, schema, message, coerce_data)
    try:
        coerced_and_validated_data = validate_against_schema(schema, data)
        return coerced_and_validated_data if coerce_data else data
    except Exception as e:
        message_details = {
            "subject": message,
            "error": "{0}: {1}".format(e.__class__.__name__, e),
            "value": data,
            "schema": schema
        }
        raise ValueError("Bad value provided for {subject}. - error: {error} schema: {schema} value: {value}".format(**message_details))

def validated(validation_predicate=None, coerce_data=True, input_schema=None, output_schema=None, fn=None):
    if fn is None:
        return partial(validated, validation_predicate, coerce_data, input_schema, output_schema)

    validation_predicate = validation_predicate or WHEN_DEBUGGING
    input_validator = validator(input_schema or IDENTITY, "input to function {0}".format(fn.__name__), coerce_data)
    output_validator = validator(output_schema or IDENTITY, "output from function {0}".format(fn.__name__), coerce_data)

    @wraps(fn)
    def _fn(*args, **kwargs):
        if validation_predicate():
            validated_args, validated_kwargs = validate_function_input(input_validator, args, kwargs)
            return output_validator(fn(*validated_args, **validated_kwargs))
        else:
            return fn(*args, **kwargs)
    return _fn

def validate_function_input(input_validator, arg_list, kwarg_dict):
    if arg_list and kwarg_dict:
        validated_input = input_validator(arg_list + tuple([kwarg_dict]))
        args, kwargs = validated_input[:-1], validated_input[-1]
    elif kwarg_dict:
        validated_input = input_validator(kwarg_dict)
        args, kwargs = [], validated_input
    elif arg_list and len(arg_list) > 1:
        validated_input = input_validator(arg_list)
        args, kwargs = validated_input, {}
    elif arg_list and len(arg_list) is 1:
        validated_input = input_validator(arg_list[0])
        args, kwargs = [validated_input], {}
    else:
        args, kwargs = arg_list, kwarg_dict
    return args, kwargs

if __name__ == '__main__':
    import operator

    my_validator = partial(validated, ALWAYS)

    @my_validator(input_schema=[int], output_schema=[date_string])
    def sum_things(*numbers):
        return reduce(operator.add, numbers)

    print sum_things(1,2,3)
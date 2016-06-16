import collections
from utils import merge_with, multiple_dispatch_fn

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

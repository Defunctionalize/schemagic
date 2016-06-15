import collections
from utils import merge_with, assert_raises, multiple_dispatch_fn

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
    return map(lambda x, y: x(y), schema, value)

is_map_template = lambda schema: isinstance(schema, collections.MutableMapping) and len(schema.items()) is 1 and not isinstance(schema.keys()[0], str)
is_keyed_mapping = lambda schema: isinstance(schema, collections.MutableMapping) and not is_map_template(schema)
is_sequence_template = lambda schema: isinstance(schema, collections.Sequence) and len(schema) is 1
is_strict_sequence = lambda schema: isinstance(schema, collections.Sequence) and 1 < len(schema)

validate_against_schema = multiple_dispatch_fn({
        is_sequence_template: validate_sequence_template,
        is_strict_sequence: validate_strict_sequence,
        is_map_template: validate_map_template,
        is_keyed_mapping: validate_keyed_mapping},
    default=lambda schema, value: schema(value))

def test_validate_against_schema():
    # test base situation, a simple function schema
    assert validate_against_schema(str, "hello")
    with assert_raises(ValueError):
        validate_against_schema(int, "hello")

    # test map template
    assert validate_against_schema({int: str}, {1: "hello", 2: "world"})
    with assert_raises():
        validate_against_schema({int: str}, {"not an int": "hello", "definitely not an int": "world"})

    # test sequence template
    assert validate_against_schema([int], [1, 2, 3])
    with assert_raises():
        validate_against_schema([int], ["not an int", 1, "is definitely not an int"])

    # test strict sequence
    assert validate_against_schema([int, int], [1, 2])
    with assert_raises():
        validate_against_schema([int, int], [1])

test_validate_against_schema()

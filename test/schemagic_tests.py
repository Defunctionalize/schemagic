from collections import defaultdict
from pprint import pprint

from schemagic.core import validate_against_schema
from schemagic.utils import separate_dict
from schemagic.validators import formatted_string

test_cases = {
    validate_against_schema: {
        "showing an error when given int instead of list of ints":
            dict(schema=[int],
                 value=5,
                 result=TypeError),
        "successfully returning unmodified list of ints":
            dict(schema=[int],
                 value=[5, 6],
                 result=[5, 6]),
    },
    formatted_string:{
        "throwing error when incorrectly formatted string passed as data":
            dict(format=r'\d+',
                 data="not a digit",
                 result=ValueError
            ),
        "returning string when properly formatted":
            dict(format=r'\d+',
                 data="112233",
                 result="112233"),
        "stringifing data before checking - and returning as string":
            dict(format=r'\d+',
                 data=112233,
                 result="112233")
    }
}

def capture_errors(fn_with_possible_errors):
    try:
        return fn_with_possible_errors()
    except Exception as e:
        return e.__class__


def run_tests(test_cases):
    test_results = defaultdict(list)
    for test_fn, test_definitions in test_cases.items():
        for test_motivation, test_definition in test_definitions.items():
            split_out_test_parameters = separate_dict(test_definition, "result", "test_motivation")
            test_kwargs, expected_result = split_out_test_parameters[0], split_out_test_parameters[1]["result"]
            test_result = capture_errors(lambda: test_fn(**test_kwargs))
            test_results[test_fn.__name__].append(test_result == expected_result or "Not {0} as expected. expected: {1} got: {2}".format(test_motivation, expected_result, test_result))
    return test_results

if __name__ == '__main__':
    map(pprint, run_tests(test_cases).items())
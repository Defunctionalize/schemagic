from collections import defaultdict
from pprint import pprint
from unittest.case import TestCase
from flask import Flask
import itertools

from schemagic.core import validate_against_schema
from schemagic.utils import separate_dict
from schemagic.validators import formatted_string, null, or_, enum
from schemagic.web import service_registry

test_cases = {
    validate_against_schema: {
        "showing an error when given int instead of list of ints":
            dict(schema=[int],
                 value=5,
                 result=TypeError),
        "returning unmodified list of ints when validating [int] template sequence":
            dict(schema=[int],
                 value=[5, 6],
                 post_process=list,
                 result=[5, 6]),
        "validating with str function with correct data":
            dict(schema=str,
                 value="hello",
                 result="hello"),
        "validating with int function with incorrect data":
            dict(schema=int,
                 value="hello",
                 result=ValueError),
        "validating map template with correct data":
            dict(schema={int: str},
                 value={1: "hello", 2: "world"},
                 result={1: "hello", 2: "world"}),
        "validating strict sequence with good data":
            dict(schema=[int, int],
                 value=[1, 2],
                 post_process=list,
                 result=[1, 2]),
        "validating strict sequence with bad data":
            dict(schema=[int, int],
                 value=[1],
                 post_process=list,
                 result=ValueError),
    },
    formatted_string(r"\d+"):{
        "throwing error when incorrectly formatted string passed as data":
            dict(data="not a digit",
                 result=ValueError
            ),
        "returning string when properly formatted":
            dict(data="112233",
                 result="112233"),
        "stringifing data before checking - and returning as string":
            dict(data=112233,
                 result="112233")
    },
    null:{
        "throws error when recieves string":
            dict(data="hello",
                 result=ValueError)
    },
    or_(int, float):{
        "allowing ints":
            dict(data=10,
                 result=10),
        "allowing floats":
            dict(data=10.5,
                 result=10.5),
        "throwing error when passed string":
            dict(data="hello",
                 result=ValueError)
    },
    enum("Hello", 5):{
        "allowing string \"Hello\"": dict(data="Hello", result="Hello"),
        "allowing int 5": dict(data=5, result=5),
        "rejecting int 6": dict(data=6, result=ValueError),
        "rejecting string \"World\"": dict(data="World", result=ValueError)
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
            split_out_test_parameters = separate_dict(test_definition, "result", "post_process")
            test_kwargs, expected_result, post_process = split_out_test_parameters[0], split_out_test_parameters[1]["result"], split_out_test_parameters[1].get("post_process", lambda x: x)
            test_result = capture_errors(lambda: post_process(test_fn(**test_kwargs)))
            test_results[test_fn.__name__].append(test_result == expected_result or "Not {0} as expected. expected: {1} got: {2}".format(test_motivation, expected_result, test_result))
    return test_results

class SchemagicTests(TestCase):
    def test_all_test_cases_passing(self):
        test_results = run_tests(test_cases)
        if not all(result is True for result in itertools.chain.from_iterable(test_results.values())):
            self.fail(test_results)

class SchemagicWebTest(TestCase):
    def setUp(self):
        test_app = Flask("testing")

        test_app.config['TESTING'] = True
        self.app = test_app
        self.test_client = test_app.test_client()

    def test_normal_flask_routing(self):
        self.app.add_url_rule("/", view_func=lambda: "Hello")
        self.test_client.get('/')

    def test_service_registry(self):
        register_test_services = service_registry(self.app)
        register_test_services(
            dict(rule="/new-route",
                 input_schema=[int],
                 output_schema=int,
                 fn=lambda *args: sum(args)
            )
        )
        bad_request = self.test_client.get("/new-route")
        self.assertEqual(bad_request._status_code, 405)

        good_request = self.test_client.post("/new-route", data="[1, 2]")
        self.assertEqual(good_request._status_code, 200)
        self.assertEqual(int(good_request.data), 3)

        bad_schema_request = self.test_client.post("/new-route", data='["Not an Int"]')
        self.assertEqual(bad_schema_request._status_code, 400)
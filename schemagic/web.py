import functools
import json
from functools import partial, update_wrapper
import collections

from flask.globals import request
from flask.wrappers import Response

from schemagic.core import validate_against_schema, validator
from schemagic.utils import multiple_dispatch_fn

ALWAYS = lambda: True
WHEN_DEBUGGING = lambda: __debug__
IDENTITY = lambda x: x

dispatch_to_fn = multiple_dispatch_fn({
    lambda fn, args: isinstance(args, basestring): lambda fn, arg_list: fn(arg_list),
    lambda fn, args: isinstance(args, collections.Sequence): lambda fn, arg_list: fn(*arg_list),
    lambda fn, args: isinstance(args, collections.MutableMapping): lambda fn, arg_list: fn(**arg_list)},
    default= lambda fn, arg_list: fn(arg_list)
)
dispatch_to_fn.__name__ = "dispatch_to_fn"

def process_error(exception):
    if "input" in exception.message:
        return Response(
            response=exception,
            status=400)
    return Response(
        status=500,
        response=exception)


def webservice_fn(fn, input_validator, output_validator):
    try:
        return Response(
            response= functools.reduce(lambda x, y: y(x),[
                json.loads,
                partial(validate_against_schema, input_validator),
                partial(dispatch_to_fn, fn),
                partial(validate_against_schema, output_validator),
                json.dumps
            ], request.data),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        return process_error(e)


def service_route(service, validation_pred=None, coerce_data=True, rule=None, input_schema=None, output_schema=None, fn=None):
    if not rule:
        return update_wrapper(partial(service_route, service, validation_pred, coerce_data), service_route)
    if fn is None:
        return update_wrapper(partial(service_route, service, validation_pred, coerce_data, rule, input_schema, output_schema), service_route)

    validation_pred = validation_pred or WHEN_DEBUGGING
    input_validator = validator(input_schema or IDENTITY, "input to endpoint {0}".format(rule), validation_predicate=validation_pred, coerce_data=coerce_data)
    output_validator = validator(output_schema or IDENTITY, "output from endpoint {0}".format(rule), validation_predicate=validation_pred, coerce_data=coerce_data)

    service.add_url_rule(
        rule=rule,
        endpoint=fn.__name__ if hasattr(fn, "__name__") else rule,
        view_func=update_wrapper(lambda: webservice_fn(fn, input_validator, output_validator), fn),
        methods=['POST']
    )
    return fn


def service_registry(service, validation_pred=None, coerce_data=True, *service_definitions):
    if not service_definitions:
        return update_wrapper(partial(service_registry, service, validation_pred, coerce_data), service_registry)
    map(lambda definition: service_route(service, validation_pred, coerce_data, **definition), service_definitions)
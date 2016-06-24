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
dispatch_to_fn.__doc__ =\
    """Dispatches a json object to a function.  The way the data is applied depends on the structure of the data.
    #. if the data is a sequence, it will unpack it and pass each item into the function, i.e. it will use *args
    #. if the data is a mapping, it will unpack it and pass in the items as keywords, i.e. it will use **kwargs
    #. if the data is anything else (i.e. it is a primitive, non iterable), it will pass it in directly.

    **NOTE** an important "gotcha" of this implementation is that a function that expects a single, iterable object
        will have to have its argument passed to it by keyword.  This causes a lot builtin functions in earlier versions
        of python to be ineligible for this kind of dispatch.  For instance, the sum function in 2.7 takes a single
        iterable argument, and that argument can not be passed by keyword.  as such, this function can not be used
        to dispatch json to the sum function in 2.7

    :param fn: the function which is to recieve the values from the arg data
    :param args: a data structure (usually rehydrated json) that is to be applied piecemeal to the function. see
        rules presented above.
    """

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
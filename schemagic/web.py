import functools
import simplejson as json
from functools import partial, update_wrapper
import collections

from flask.globals import request
from flask.wrappers import Response

from schemagic.core import validate_against_schema, validator
from schemagic.utils import multiple_dispatch_fn, is_string

_ALWAYS = lambda: True
_WHEN_DEBUGGING = lambda: __debug__
_IDENTITY = lambda x: x

_dispatch_to_fn = multiple_dispatch_fn({
    lambda fn, args: is_string(args): lambda fn, arg_list: fn(arg_list),
    lambda fn, args: isinstance(args, collections.Sequence): lambda fn, arg_list: fn(*arg_list),
    lambda fn, args: isinstance(args, collections.MutableMapping): lambda fn, arg_list: fn(**arg_list)},
    default=lambda fn, arg_list: fn(arg_list)
)
dispatch_to_fn = lambda fn, args: _dispatch_to_fn(fn, args)
dispatch_to_fn.__doc__ = \
    """Dispatches a json object to a function.  The way the data is applied depends on the structure of the data.
        * if the data is a sequence, it will unpack it and pass each item into the function, i.e. it will use ``*args``
        * if the data is a mapping, it will unpack it and pass in the items as keywords, i.e. it will use ``**kwargs``
        * if the data is anything else (i.e. it is a primitive, non iterable), it will pass it in directly.

    **NOTE**
        an important "gotcha" of this implementation is that a function that expects a single, iterable object
        will have to have its argument passed to it by keyword.  This causes a lot builtin functions in earlier versions
        of python to be ineligible for this kind of dispatch.  For instance, the sum function in 2.7 takes a single
        iterable argument, and that argument can not be passed by keyword.  as such, this function can not be used
        to dispatch json to the sum function in 2.7

    :param fn: the function which is to recieve the values from the arg data
    :param args: a data structure (usually rehydrated json) that is to be applied piecemeal to the function. see
        rules presented above.
    """


def _process_error(exception):
    """Decomposition of the webservice fn handler.  returns 400 if the exception occurred in the input validation

    :param exception: The Exception which occured as a part of processing the request
    :return: a flask Response that more specifically identifies the cause of the problem.
    """
    if "input" in exception.args[0]:
        return Response(
            response=exception,
            status=400)
    return Response(
        status=500,
        response=exception)


def webservice_fn(fn, input_validator, output_validator):
    """Handles the minutia of pulling data from the request object and passing it into the function and validators

    :param fn: the function which is supposed to fulfill the contract defined by the input and output schemata
    :param input_validator: a ``validator`` as described in the core function of the same name
    :param output_validator: a ``validator`` as described in the core function of the same name
    :return: a json Flask Response that contains either the requested data or an error.
    """
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
        return _process_error(e)


def service_route(service, validation_pred=None, coerce_data=True, rule=None, input_schema=None, output_schema=None, fn=None):
    """Function decorator that registers a ``webservice_fn`` version of the function on the provided service.

    Note that this function is used primarily to register functions en masse with the ``service_registry`` interface.
    However, it can be used as a traditional decorator if desired. e.g.:

    .. code_block:: python

        my_service_route = partial(service_route, my_service)

        @my_service_route(rule="/this-route", input_schema=[int], output_schema=int)
        def my_sum(*ints):
            return sum(ints)

    I find there to be 2 important pitfalls to bear in mind if using the decorator this way:
    1. This makes it seem like the function is being somehow modified, which it is not.
       It can confuse people reading your code into thinking they have to make separate, dedicated webservice versions
       of the function in order to register them.
    2. It becomes unsafe to use positional arguments when using the decorator like this.  If I had defined that decorator
       using the canonical flask pattern, e.g. ``@my_service_route("/this-route")`` it would have caused everything to
       explode.  To get consistent behavior, you MUST specify the arguments by keyword.

    :param service: The service or app which is to have the rule added to it. Must support the ``add_url_rule`` interface
        as described in the `flask documentation <http://flask.pocoo.org/docs/0.11/api/>`_.

    :param validation_pred: see description in ``validator`` fn of the same param.  function that returns true or false
        The default value for validation on webservice routes is to use the value of ``__debug__`` as a guide.
    :param coerce_data: see description in ``validator`` fn of the same param.  boolean flag for coercing data.
        The default is to coerce data.  This is often very helpful in parsing json from a web request.
    :param rule: the url route to use when accessing this function
    :param input_schema: a data definition as described in the ``validate_against_schema`` fn documentation.
        This value is not required.  If none is given, no validation will be done on the input.
    :param output_schema: a data definition as decribed in the ``validate_against_schema`` fn documentation.
        This value is not required.  If none is given, no validation will be done on the output.
    :param fn: The function intended to implement the request.
    :return: the original function, unmodified.
    """
    if not rule:
        return update_wrapper(partial(service_route, service, validation_pred, coerce_data), service_route)
    if fn is None:
        return update_wrapper(partial(service_route, service, validation_pred, coerce_data, rule, input_schema, output_schema), service_route)

    validation_pred = validation_pred or _WHEN_DEBUGGING
    input_validator = validator(input_schema or _IDENTITY, "input to endpoint {0}".format(rule), validation_predicate=validation_pred, coerce_data=coerce_data)
    output_validator = validator(output_schema or _IDENTITY, "output from endpoint {0}".format(rule), validation_predicate=validation_pred, coerce_data=coerce_data)

    service.add_url_rule(
        rule=rule,
        endpoint=fn.__name__ if hasattr(fn, "__name__") else rule,
        view_func=update_wrapper(lambda: webservice_fn(fn, input_validator, output_validator), fn),
        methods=['POST']
    )
    return fn


def service_registry(service, validation_pred=None, coerce_data=True, *service_definitions):
    """Registers all the service descriptions provided on the app specified by the ``service`` parameter.

    :param service: Service to register functions on. see description of same parameter in ``service_route`` documentation.
    :param validation_pred: function returning boolean. see description of same parameter in ``service_route`` documentation.
    :param coerce_data: boolean. see description of same parameter in ``service_route`` documentation.
    :param service_definitions: mappings that contain the keyword args to service_route.
    :return: if service definitions not provided, returns the a function that accepts service definitions.
            if service definitions provided, returns nothing.
    """
    if not service_definitions:
        return update_wrapper(partial(service_registry, service, validation_pred, coerce_data), service_registry)
    list(map(lambda definition: service_route(service, validation_pred, coerce_data, **definition), service_definitions))
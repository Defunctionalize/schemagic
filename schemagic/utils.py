import copy
import doctest
import functools
from contextlib import contextmanager
from functools import wraps, update_wrapper, partial

import operator

import itertools


def merge_with(fn, a, b):
    """ returns a new dictionary that is the merger of a and b.  applies fn to the values of colliding keys.

    >>> merge_with(operator.add, {"a": 1}, {"a": 1, "b": 1})
    {'a': 2, 'b': 1}
    """
    fresh_dict = copy.deepcopy(a)
    for k, v in b.items():
        if k in fresh_dict:
            fresh_dict[k] = fn(fresh_dict[k], v)
        else:
            fresh_dict[k] = v
    return fresh_dict

merge = partial(merge_with, lambda a, b: b)
merge.__name__ = "merge"

def multiple_dispatch_fn(dispatch_map, default=None):
    """
    creates a multiple dispatch function.

    returns a function whose implementation of the function is based on the arguments passed to it.  it decides
    what implementation to use by testing the arguments against a series of predicates to detect what situation
    is applicable.

    For example,

    >>> add_if_ints_multiply_if_floats = multiple_dispatch_fn(
    ... {lambda *nums: all(isinstance(num, int) for num in nums): operator.add,
    ...  lambda *nums: all(isinstance(num, float) for num in nums): operator.mul})
    >>> add_if_ints_multiply_if_floats(10, 10)
    20
    >>> add_if_ints_multiply_if_floats(10.0, 10.0)
    100.0

    You can also provide a default implementation to use if none of the predicates match.
    For example,

    >>> add_if_ints_else_return_unmodified = multiple_dispatch_fn(
    ... {lambda *nums: all(isinstance(num, int) for num in nums): operator.add},
    ...  default=lambda *items: items)
    >>> add_if_ints_else_return_unmodified(25, 25)
    50
    >>> add_if_ints_else_return_unmodified("hello", None)
    ('hello', None)

    :param dispatch_map: mapping {predicate_fn: implementation_fn}
    :param default: implementation fn to be used if none of the predicates are satisfied
    :return:
    """
    dispatch_map = dispatch_map or {}
    def _fn(*args, **kwargs):
        try:
            dispatch_fn = next(itertools.chain([value for key, value in dispatch_map.items() if key(*args, **kwargs)],
                                               [default] if default else []))
            return dispatch_fn(*args, **kwargs)
        except StopIteration:
            raise ValueError("No dispatch function found. args: {0}, kwargs: {1}".format(args, kwargs))
    return _fn

def remove_key(dict_, key):
    del dict_[key]
    return dict_

def separate_dict(initial_dict, *keys_to_remove):
    """returns 2 new dicts, one with some keys removed, and another with only those keys"""
    part1, part2 = copy.copy(initial_dict), {}
    for key, val in part1.items():
        if key in keys_to_remove:
            part2[key] = val

    return functools.reduce(remove_key, part2.keys(), part1), part2

def is_string(obj):
    try:
        return isinstance(obj, basestring)
    except NameError:
        return isinstance(obj, str)

@contextmanager
def assert_raises(expected_error=None):
    try:
        yield
    except Exception as e:
        if expected_error:
            assert isinstance(e, expected_error), "Expected to raise type(s): {0}, raised {1} instead".format(expected_error, e.__class__.__name__)
        else:
            # No specific error raised, so we're good.
            pass
    else:
        raise AssertionError("No exception raised")

if __name__ == '__main__':
    doctest.testmod()
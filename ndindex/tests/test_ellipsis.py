from numpy import arange

from hypothesis import given
from hypothesis.strategies import one_of, integers

from pytest import raises

from ..ndindex import ndindex
from ..tuple import Tuple
from ..integer import Integer
from ..ellipsis import ellipsis
from .helpers import check_same, prod, shapes, ellipses

def test_ellipsis_exhaustive():
    for n in range(10):
        a = arange(n)
    check_same(a, ...)

@given(ellipses(), shapes)
def test_ellipsis_hypothesis(idx, shape):
    a = arange(prod(shape)).reshape(shape)
    check_same(a, idx)

def test_ellipsis_reduce_exhaustive():
    for n in range(10):
        a = arange(n)
        check_same(a, ..., ndindex_func=lambda a, x: a[x.reduce((n,)).raw])

@given(ellipses(), shapes)
def test_ellipsis_reduce_hypothesis(idx, shape):
    a = arange(prod(shape)).reshape(shape)
    check_same(a, idx, ndindex_func=lambda a, x: a[x.reduce(shape).raw])

def test_ellipsis_reduce_no_shape_exhaustive():
    for n in range(10):
        a = arange(n)
        check_same(a, ..., ndindex_func=lambda a, x: a[x.reduce().raw])

@given(ellipses(), shapes)
def test_ellipsis_reduce_no_shape_hypothesis(idx, shape):
    a = arange(prod(shape)).reshape(shape)
    check_same(a, idx, ndindex_func=lambda a, x: a[x.reduce().raw])

@given(ellipses(), one_of(shapes, integers(0, 10)))
def test_ellipsis_newshape_hypothesis(idx, shape):
    if isinstance(shape, int):
        a = arange(shape)
    else:
        a = arange(prod(shape)).reshape(shape)

    def raw_func(a, idx):
        return a[idx].shape

    def ndindex_func(a, index):
        return index.newshape(shape)

    def assert_equal(raw_shape, newshape):
        assert raw_shape == newshape

    check_same(a, idx, raw_func=raw_func, ndindex_func=ndindex_func,
               assert_equal=assert_equal, same_exception=False)

def test_ellipsis_newshape_ndindex_input():
    raises(TypeError, lambda: ellipsis().newshape(Tuple(2, 1)))
    raises(TypeError, lambda: ellipsis().newshape(Integer(2)))

@given(ellipses(), one_of(shapes, integers(0, 10)))
def test_ellipsis_isempty_hypothesis(idx, shape):
    if isinstance(shape, int):
        a = arange(shape)
    else:
        a = arange(prod(shape)).reshape(shape)

    index = ndindex(idx)

    def raw_func(a, idx):
        return a[idx].size == 0

    def ndindex_func(a, index):
        return index.isempty(), index.isempty(shape)

    def assert_equal(raw_empty, ndindex_empty):
        isempty, isempty_shape = ndindex_empty

        # Since idx is an ellipsis, it should never be unconditionally empty
        assert not isempty
        # We cannot test the converse with hypothesis. isempty may be False
        # but a[idx] could still be empty for this specific a (e.g., if a is
        # already itself empty).

        # isempty() should always give the correct result for a specific
        # array after reduction
        assert isempty_shape == raw_empty, (index, shape)

    check_same(a, idx, raw_func=raw_func, ndindex_func=ndindex_func,
               assert_equal=assert_equal, same_exception=False)
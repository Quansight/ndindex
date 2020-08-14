from pytest import raises

from numpy import arange, isin, bool_

from hypothesis import given, assume, example
from hypothesis.strategies import integers, one_of

from ..slice import Slice
from ..tuple import Tuple
from ..integer import Integer
from ..ellipsis import ellipsis
from .helpers import check_same, slices, prod, shapes, iterslice, assert_equal

def test_slice_args():
    # Test the behavior when not all three arguments are given
    # TODO: Incorporate this into the normal slice tests
    raises(TypeError, lambda: slice())
    raises(TypeError, lambda: Slice())
    raises(TypeError, lambda: Slice(1.0))
    # See docstring of operator_index()
    raises(TypeError, lambda: Slice(True))
    raises(TypeError, lambda: Slice(bool_(True)))

    S = Slice(1)
    assert S == Slice(S) == Slice(None, 1) == Slice(None, 1, None) == Slice(None, 1, None)
    assert S.raw == slice(None, 1, None)
    assert S.args == (S.start, S.stop, S.step)

    S = Slice(0, 1)
    assert S == Slice(S) == Slice(0, 1, None)
    assert S.raw == slice(0, 1, None)
    assert S.args == (S.start, S.stop, S.step)

    S = Slice(0, 1, 2)
    assert S == Slice(S)
    assert S.raw == slice(0, 1, 2)
    assert S.args == (S.start, S.stop, S.step)

def test_slice_exhaustive():
    for n in range(100):
        a = arange(n)
        for start, stop, step in iterslice(one_two_args=False):
            check_same(a, slice(start, stop, step))

@given(slices(), integers(0, 100))
def test_slice_hypothesis(s, size):
    a = arange(size)
    check_same(a, s)

def test_slice_len_exhaustive():
    for args in iterslice():
        try:
            S = Slice(*args)
        except ValueError:
            continue
        try:
            l = len(S)
        except ValueError:
            # No maximum
            l = 10000

        m = -1
        for n in range(20):
            a = arange(n)
            L = len(a[S.raw])
            assert L <= l, S
            m = max(L, m)
        if l != 10000:
            assert m == l, S
        else:
            # If there is no maximum, the size of the slice should increase
            # with larger arrays.
            assert len(arange(30)[S.raw]) > m, S

        # TODO
        # if l == 0:
        #     # There should only be one canonical length 0 slice
        #     assert s == Slice(0, 0)

@given(slices())
def test_slice_len_hypothesis(s):
    try:
        S = Slice(s)
    except ValueError: # pragma: no cover
        assume(False)
    try:
        l = len(S)
    except ValueError:
        # No maximum
        l = 10000

    m = -1
    for n in range(20):
        a = arange(n)
        L = len(a[S.raw])
        assert L <= l, (S, n)
        m = max(L, m)
    if l != 10000:
        assert m == l, S
    else:
        # If there is no maximum, the size of the slice should increase
        # with larger arrays.
        assert len(arange(30)[S.raw]) > m, S

def test_slice_args_reduce_no_shape():
    S = Slice(1).reduce()
    assert S == Slice(None, 1).reduce() == Slice(0, 1, None).reduce() == Slice(0, 1).reduce() == Slice(0, 1, 1)

    S = Slice(0, 1).reduce()
    assert S == Slice(0, 1, None).reduce() == Slice(0, 1, 1)

def test_slice_reduce_no_shape_exhaustive():
    for n in range(10):
        a = arange(n)
        for args in iterslice():
            try:
                S = Slice(*args)
            except ValueError:
                continue

            check_same(a, S.raw, ndindex_func=lambda a, x: a[x.reduce().raw])

            # Check the conditions stated by the Slice.reduce() docstring
            reduced = S.reduce()
            # TODO: Test that start and stop are not None when possible
            assert reduced.step != None

@given(slices(), shapes)
def test_slice_reduce_no_shape_hypothesis(s, shape):
    a = arange(prod(shape)).reshape(shape)
    try:
        S = Slice(s)
    except ValueError: # pragma: no cover
        assume(False)

    # The axis argument is tested implicitly in the Tuple.reduce test. It is
    # difficult to test here because we would have to pass in a Tuple to
    # check_same.
    check_same(a, S.raw, ndindex_func=lambda a, x: a[x.reduce().raw])

    # Check the conditions stated by the Slice.reduce() docstring
    reduced = S.reduce()
    # TODO: Test that start and stop are not None when possible
    assert reduced.step != None

def test_slice_reduce_exhaustive():
    for n in range(10):
        a = arange(n)
        for args in iterslice():
            try:
                S = Slice(*args)
            except ValueError:
                continue

            check_same(a, S.raw, ndindex_func=lambda a, x: a[x.reduce((n,)).raw])

            # Check the conditions stated by the Slice.reduce() docstring
            # TODO: Factor this out so we can also test it in the tuple reduce
            # tests.
            reduced = S.reduce((n,))
            assert reduced.start >= 0
            # We cannot require stop > 0 because if stop = None and step < 0, the
            # only equivalent stop that includes 0 is negative.
            assert reduced.stop != None
            assert reduced.step != None
            assert len(reduced) == len(a[reduced.raw]), (S, n)

@given(slices(), one_of(shapes, integers(0, 10)))
def test_slice_reduce_hypothesis(s, shape):
    if isinstance(shape, int):
        a = arange(shape)
    else:
        a = arange(prod(shape)).reshape(shape)

    try:
        S = Slice(s)
    except ValueError: # pragma: no cover
        assume(False)

    # The axis argument is tested implicitly in the Tuple.reduce test. It is
    # difficult to test here because we would have to pass in a Tuple to
    # check_same.
    check_same(a, S.raw, ndindex_func=lambda a, x: a[x.reduce(shape).raw])

    # Check the conditions stated by the Slice.reduce() docstring
    try:
        reduced = S.reduce(shape)
    except IndexError:
        # shape == ()
        return

    assert reduced.start >= 0
    # We cannot require stop > 0 because if stop = None and step < 0, the
    # only equivalent stop that includes 0 is negative.
    assert reduced.stop != None
    assert reduced.step != None
    assert len(reduced) == len(a[reduced.raw]), (S, shape)


def test_slice_newshape_exhaustive():
    def raw_func(a, idx):
        return a[idx].shape

    def ndindex_func(a, index):
        return index.newshape(shape)

    def assert_equal(raw_shape, newshape):
        assert raw_shape == newshape

    for n in range(10):
        shape = n
        a = arange(n)

        for sargs in iterslice():
            try:
                S = Slice(*sargs)
            except ValueError:
                continue

            check_same(a, S.raw, raw_func=raw_func, ndindex_func=ndindex_func,
                   assert_equal=assert_equal)

@given(slices(), one_of(shapes, integers(0, 10)))
def test_slice_newshape_hypothesis(s, shape):
    if isinstance(shape, int):
        a = arange(shape)
    else:
        a = arange(prod(shape)).reshape(shape)

    try:
        Slice(s)
    except ValueError: # pragma: no cover
        assume(False)


    def raw_func(a, idx):
        return a[idx].shape

    def ndindex_func(a, index):
        return index.newshape(shape)

    def assert_equal(raw_shape, newshape):
        assert raw_shape == newshape

    check_same(a, s, raw_func=raw_func, ndindex_func=ndindex_func,
               assert_equal=assert_equal)

def test_slice_newshape_ndindex_input():
    raises(TypeError, lambda: Slice(6).newshape(Tuple(2, 1)))
    raises(TypeError, lambda: Slice(6).newshape(Integer(2)))

def test_slice_as_subindex_slice_exhaustive():
    # We have to restrict the range of the exhaustive test to get something
    # that finishes in a reasonable amount of time (~30 seconds, vs. 30
    # minutes for the original ranges).

    # a = arange(10)
    # for sargs in iterslice():
    #     for indexargs in iterslice():

    a = arange(5)
    for sargs in iterslice((-5, 5), (-5, 5), (-5, 5), one_two_args=False):
        for indexargs in iterslice((-5, 5), (-5, 5), (-5, 5), one_two_args=False):

            try:
                S = Slice(*sargs)
            except ValueError:
                continue

            try:
                Index = Slice(*indexargs)
            except ValueError:
                continue

            try:
                Subindex = S.as_subindex(Index)
            except NotImplementedError:
                continue

            aS = a[S.raw]
            aindex = a[Index.raw]
            asubindex = aindex[Subindex.raw]

            assert_equal(asubindex, aS[isin(aS, aindex)])

            subindex2 = Index.as_subindex(S)
            asubindex2 = aS[subindex2.raw]
            assert_equal(asubindex2, asubindex)

def test_slice_as_subindex_integer_exhaustive():
    a = arange(10)
    for sargs in iterslice():
        for i in range(-10, 10):

            try:
                S = Slice(*sargs)
            except ValueError:
                continue

            Index = Integer(i)

            empty = False
            try:
                Subindex = S.as_subindex(Index)
            except NotImplementedError:
                continue
            except ValueError as e:
                assert "do not intersect" in e.args[0]
                empty = True

            aS = a[S.raw]
            aindex = a[i]

            if empty:
                assert not isin(aS, aindex).any()
                assert not isin(aindex, aS).any()
                with raises(ValueError, match="do not intersect"):
                    Index.as_subindex(S)
            else:
                asubindex = aindex[Subindex.raw]

                assert_equal(asubindex.flatten(), aS[isin(aS, aindex)])

                subindex2 = Index.as_subindex(S)
                asubindex2 = aS[subindex2.raw]
                assert_equal(asubindex2, asubindex)

def test_slice_as_subindex_ellipsis_exhaustive():
    a = arange(10)
    for sargs in iterslice():
        try:
            S = Slice(*sargs)
        except ValueError:
            continue

        Index = ellipsis()

        try:
            Subindex = S.as_subindex(Index)
        except NotImplementedError:
            continue

        aS = a[S.raw]
        aindex = a[...]

        asubindex = aindex[Subindex.raw]

        assert_equal(asubindex.flatten(), aS[isin(aS, aindex)])

        try:
            subindex2 = Index.as_subindex(S)
        except NotImplementedError:
            continue
        asubindex2 = aS[subindex2.raw]
        assert_equal(asubindex2, asubindex)

def test_slice_isempty_exhaustive():
    for args in iterslice():
        try:
            S = Slice(*args)
        except ValueError:
            continue

        isempty = S.isempty()

        aempty = True
        for n in range(30):
            a = arange(n)

            aS = a[S.raw]
            if aS.size != 0:
                if isempty:
                    raise AssertionError(f"Slice s = {S}.isempty() gave True, a[s] is not empty for a = range({n}).")
                else:
                    aempty = False
            # isempty() should always give the correct result for a specific
            # array shape
            assert S.isempty(n) == (aS.size == 0)

        assert isempty == aempty, S

@example(slice(None, None, None), ())
@given(slices(), one_of(shapes, integers(0, 10)))
def test_slice_isempty_hypothesis(s, shape):
    if isinstance(shape, int):
        a = arange(shape)
    else:
        a = arange(prod(shape)).reshape(shape)

    try:
        S = Slice(s)
    except (IndexError, ValueError): # pragma: no cover
        assume(False)

    def raw_func(a, s):
        return a[s].size == 0

    def ndindex_func(a, S):
        return S.isempty(), S.isempty(shape)

    def assert_equal(raw_empty, ndindex_empty):
        isempty, isempty_shape = ndindex_empty

        # If isempty is True then a[t] should be empty
        if isempty:
            assert raw_empty, (S, shape)
        # We cannot test the converse with hypothesis. isempty may be False
        # but a[s] could still be empty for this specific a (e.g., if a is
        # already itself empty).

        # If isempty is true with no shape it should be true for a specific
        # shape. The converse is not true because the indexed array could be
        # empty.
        if isempty:
            assert isempty_shape, (S, shape)

        # isempty() should always give the correct result for a specific
        # array after reduction
        assert isempty_shape == raw_empty, (S, shape)

    check_same(a, s, raw_func=raw_func, ndindex_func=ndindex_func,
               assert_equal=assert_equal, same_exception=False)
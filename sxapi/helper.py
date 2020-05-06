#!/usr/bin/python
# coding: utf8

import datetime
import collections
import time
import functools
import pendulum


def toTS(dt):
    if isinstance(dt, pendulum.DateTime):
        base = dt.replace(year=1970, month=1, day=1, hour=0,
                          minute=0, second=0, microsecond=0)
        return int((dt - base).total_seconds())
    if isinstance(dt, datetime.datetime):
        return int((dt - datetime.datetime(1970, 1, 1)).total_seconds())
    if isinstance(dt, datetime.date):
        return int((dt - datetime.datetime(1970, 1, 1)).total_seconds())
    return int(dt)


def fromTS(ts, timezone=None, tz_aware=True):
    time_tuple = time.gmtime(ts)
    if not tz_aware:
        return datetime.datetime(
            year=time_tuple.tm_year,
            month=time_tuple.tm_mon,
            day=time_tuple.tm_mday,
            hour=time_tuple.tm_hour,
            minute=time_tuple.tm_min,
            second=time_tuple.tm_sec,
            microsecond=0,
        )
    if timezone is None:
        timezone = "UTC"
    return pendulum.datetime(
        year=time_tuple.tm_year,
        month=time_tuple.tm_mon,
        day=time_tuple.tm_mday,
        hour=time_tuple.tm_hour,
        minute=time_tuple.tm_min,
        second=time_tuple.tm_sec,
        microsecond=0,
        tz=timezone
    )


def splitDateRange(start, end, days):
    assert start <= end
    f = toTS(start)
    t = toTS(end)
    diff = days * 24 * 60 * 60
    last = f
    # left = end - start
    for i in range(f, t - diff, diff):
        last = i + diff - 1
        yield (fromTS(i), fromTS(last))
    if last < t:
        yield (fromTS(last + 1), fromTS(t))


def splitTimeRange(start, end, days):
    assert start <= end
    f = int(start)
    t = int(end)
    diff = days * 24 * 60 * 60
    last = f
    # left = end - start
    for i in range(f, t - diff, diff):
        last = i + diff - 1
        yield (i, last)
    if last < t:
        yield (last + 1, t)


class Memoize(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

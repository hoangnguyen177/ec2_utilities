# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import time, math

# Retry decorator with exponential backoff
def retry(tries, delay=2, backoff=2):
    """Retries a function or method until it returns something that
    evaluates to True.
    
    delay sets the initial delay, and backoff sets how much the delay should
    lengthen after each failure. backoff must be greater than 1, or else it
    isn't really a backoff. tries must be at least 1, and delay greater than
    0.
    
    Usage:
        @retry(3)
        def might_fail(...):
            ...
        or with lambda functions e.g.
        retry(3)(lambda: False)()"""

    if backoff <= 1:
        raise ValueError("backoff must be greater than 1")

    tries = math.floor(tries)
    if tries < 1:
        raise ValueError("tries must be 1 or greater")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay # make mutable
            rv = f(*args, **kwargs) # 1st try
            if rv:
                return rv
            mtries -= 1
            while mtries > 0:
                mtries -= 1
                time.sleep(mdelay)
                mdelay *= backoff
                rv = f(*args, **kwargs)
                if rv:
                    return rv
            return False
        return f_retry # true decorator -> decorated function
    return deco_retry  # @retry(arg[, ...]) -> true decorator

# Retry decorator with exponential backoff
def retry_with_catch(retries, delay=2, backoff=2, delay_ceiling=0,
        reraise_excs=(), suppress_excs=()):
    """Retries a function or method until it returns something True,
    optionally reraising or suppressing specified exceptions.
    
    delay sets the initial delay, backoff sets by how many times delay should
    lengthen after each failure. delay_ceiling caps the delay period.
    reraise_excs is a tuple of exception types that should be re-raised
    immediately if caught during execution of the decorated function.
    suppress_excs is a tuple of exception types that should ignored until
    retries is exhausted. if suppress_excs is specified and reraise_excs is
    not then any other exception not explicitly suppressed will be raised.
    
    Usage:
        @retry(3)
        def might_fail(...):
            ...
        or with lambda functions e.g.
        retry(3)(lambda: False)()"""

    if backoff <= 1:
        raise ValueError("backoff must be greater than 1")

    retries = math.floor(retries)
    if retries < 1:
        raise ValueError("retries must be 1 or greater")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    if delay_ceiling < 0:
        raise ValueError("delay_ceiling must be >= 0")

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = retries, delay # make mutable
            while mtries > 0:
                #print 'retry'
                mtries -= 1
                if delay_ceiling and mdelay > delay_ceiling:
                    mdelay = delay_ceiling
                try:
                    rv = f(*args, **kwargs)
                    if rv is not False:
                        return rv
                except reraise_excs:
                    raise
                except suppress_excs:
                    pass
                except:
                    if suppress_excs and not reraise_excs:
                        # if we get an exception not explicitly suppressed when
                        # suppress_excs is used then it should be raised
                        raise
                    if mtries == 0:
                        # if we've exhausted retries and have been hitting
                        # exceptions that aren't explicitly suppressed then
                        # we raise the last exception we got
                        raise
                    else:
                        pass
                finally:
                    time.sleep(mdelay)
                    mdelay *= backoff
                   #print 'retry'
                    mtries -= 1
                    time.sleep(mdelay)
                    mdelay *= backoff

            return False
        return f_retry # true decorator -> decorated function
    return deco_retry  # @retry(arg[, ...]) -> true decorator


# Retry decorator with exponential backoff
def ioretry(tries, delay=2, backoff=2):
    """Retries a function or method until it returns something that
    does not evaluate to False (i.e., empty lists, tuples are OK).

    delay sets the initial delay, and backoff sets how much the delay should
    lengthen after each failure. backoff must be greater than 1, or else it
    isn't really a backoff. tries must be at least 1, and delay greater than
    0.
    
    Usage:
        @retry(3)
        def might_fail(...):
            ...
        or with lambda functions e.g.
        retry(3)(lambda: False)()"""

    if backoff <= 1:
        raise ValueError("backoff must be greater than 1")

    tries = math.floor(tries)
    if tries < 1:
        raise ValueError("tries must be 1 or greater")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay # make mutable
            try:
                rv = f(*args, **kwargs) # 1st try
                if rv:
                    return rv
            except:
                mtries -= 1
            while mtries > 0:
                print 'retry'
                mtries -= 1
                time.sleep(mdelay)
                mdelay *= backoff
                try:
                    rv = f(*args, **kwargs)
                    if rv:
                        return rv
                except:
                    if mtries == 0:
                        raise
                    else:
                        pass

            return False
        return f_retry # true decorator -> decorated function
    return deco_retry  # @retry(arg[, ...]) -> true decorator

@ioretry(4)
def test2():
    raise Exception('Blair')
    global cnt
    print 'test2'
    cnt += 1
    if cnt == 3:
        return cnt
    else:
        return False

from collections import deque

def lru_cache(maxsize):
    '''Decorator applying a least-recently-used cache with the given maximum size.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    '''
    def decorating_function(f):
        cache = {}              # mapping of args to results
        queue = deque()         # order that keys have been accessed
        refcount = {}           # number of times each key is in the access queue
        def wrapper(*args):
            
            # localize variable access (ugly but fast)
            _cache=cache; _len=len; _refcount=refcount; _maxsize=maxsize
            queue_append=queue.append; queue_popleft = queue.popleft

            # get cache entry or compute if not found
            try:
                result = _cache[args]
                wrapper.hits += 1
            except KeyError:
                result = _cache[args] = f(*args)
                wrapper.misses += 1

            # record that this key was recently accessed
            queue_append(args)
            _refcount[args] = _refcount.get(args, 0) + 1

            # Purge least recently accessed cache contents
            while _len(_cache) > _maxsize:
                k = queue_popleft()
                _refcount[k] -= 1
                if not _refcount[k]:
                    del _cache[k]
                    del _refcount[k]
    
            # Periodically compact the queue by duplicate keys
            if _len(queue) > _maxsize * 4:
                for i in [None] * _len(queue):
                    k = queue_popleft()
                    if _refcount[k] == 1:
                        queue_append(k)
                    else:
                        _refcount[k] -= 1
                assert len(queue) == len(cache) == len(refcount) == sum(refcount.itervalues())

            return result
        wrapper.__doc__ = f.__doc__
        wrapper.__name__ = f.__name__
        wrapper.hits = wrapper.misses = 0
        return wrapper
    return decorating_function

### {{{ http://code.activestate.com/recipes/577028/ (r6)
#import multiprocessing as MP
#from sys import exc_info
#from time import clock
#
#DEFAULT_TIMEOUT = 60
#
#################################################################################
#
#def timeout(limit=None):
#    if limit is None:
#        limit = DEFAULT_TIMEOUT
#    if limit <= 0:
#        raise ValueError()
#    def wrapper(function):
#        return _Timeout(function, limit)
#    return wrapper
#
#class TimeoutError(Exception): pass
#
#################################################################################
#
#def _target(queue, function, *args, **kwargs):
#    try:
#        queue.put((True, function(*args, **kwargs)))
#    except:
#        queue.put((False, exc_info()[1]))
#
#class _Timeout:
#
#    def __init__(self, function, limit):
#        self.__limit = limit
#        self.__function = function
#        self.__timeout = clock()
#        self.__process = MP.Process()
#        self.__queue = MP.Queue()
#
#    def __call__(self, *args, **kwargs):
#        self.cancel()
#        self.__queue = MP.Queue(1)
#        args = (self.__queue, self.__function) + args
#        self.__process = MP.Process(target=_target, args=args, kwargs=kwargs)
#        self.__process.daemon = True
#        self.__process.start()
#        self.__timeout = self.__limit + clock()
#
#    def cancel(self):
#        if self.__process.is_alive():
#            self.__process.terminate()
#
#    @property
#    def ready(self):
#        if self.__queue.full():
#            return True
#        elif not self.__queue.empty():
#            return True
#        elif self.__timeout < clock():
#            self.cancel()
#        else:
#            return False
#
#    @property
#    def value(self):
#        if self.ready is True:
#            flag, load = self.__queue.get()
#            if flag:
#                return load
#            raise load
#        raise TimeoutError()
#
#    def __get_limit(self):
#        return self.__limit
#
#    def __set_limit(self, value):
#        if value <= 0:
#            raise ValueError()
#        self.__limit = value
#
#    limit = property(__get_limit, __set_limit)
### end of http://code.activestate.com/recipes/577028/ }}}

## {{{ http://code.activestate.com/recipes/577853/ (r1)
"""
Code to timeout with processes.

>>> @timeout(.5)
... def sleep(x):
...     print "ABOUT TO SLEEP {0} SECONDS".format(x)
...     time.sleep(x)
...     return x

>>> sleep(1)
Traceback (most recent call last):
   ...
TimeoutException: timed out after 0 seconds

>>> sleep(.2)
0.2

>>> @timeout(.5)
... def exc():
...     raise Exception('Houston we have problems!')

>>> exc()
Traceback (most recent call last):
   ...
Exception: Houston we have problems!

"""
import multiprocessing
import time


class TimeoutException(Exception):
    pass


class RunableProcessing(multiprocessing.Process):
    def __init__(self, func, *args, **kwargs):
        self.queue = multiprocessing.Queue(maxsize=1)
        args = (func,) + args
        multiprocessing.Process.__init__(self, target=self.run_func, args=args, kwargs=kwargs)

    def run_func(self, func, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            self.queue.put((True, result))
        except Exception as e:
            self.queue.put((False, e))

    def done(self):
        return self.queue.full()

    def result(self):
        return self.queue.get()


def timeout(seconds, force_kill=True):
    def wrapper(function):
        def inner(*args, **kwargs):
            now = time.time()
            proc = RunableProcessing(function, *args, **kwargs)
            proc.start()
            proc.join(seconds)
            if proc.is_alive():
                if force_kill:
                    proc.terminate()
                runtime = int(time.time() - now)
                raise TimeoutException('timed out after {0} seconds'.format(runtime))
            assert proc.done()
            success, result = proc.result()
            if success:
                return result
            else:
                raise result
        return inner
    return wrapper
## end of http://code.activestate.com/recipes/577853/ }}}

if __name__=='__main__':
    @timeout(3)
    def s():
        print 'asleep'
        time.sleep(5)
        print 'awake'
    #s()
    timeout(4)(lambda: time.sleep(5))()

    global cnt
    cnt = 0
    print test2()
    print retry(5)(lambda: False)()

    @lru_cache(maxsize=20)
    def f(x, y):
        return 3*x+y
    domain = range(5)
    from random import choice
    for i in range(1000):
        r = f(choice(domain), choice(domain))
    print f.hits, f.misses

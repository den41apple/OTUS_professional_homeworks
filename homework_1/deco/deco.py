#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Callable, Any
from functools import wraps, update_wrapper


def disable(func: Callable) -> Callable:
    """
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        return func(*args, **kwargs)

    return wrapper


def decorator(deco_func: Callable) -> Callable:
    """
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    """

    def wrapper(func: Callable) -> Any:
        # Не сработало с countcalls так же как и @wraps
        return update_wrapper(deco_func(func), func)

    return wrapper


class Counter:
    """Счетчик"""
    cnt = 0

    def __add__(self, other: int) -> int:
        self.cnt += other
        return self

    def __str__(self):
        return str(self.cnt)

    def __repr__(self):
        return str(self)


@decorator
def countcalls(func: Callable) -> Callable:
    """
    Decorator that counts calls made to the function decorated.
    """
    func.calls = Counter()

    def wrapper(*args, **kwargs) -> Any:
        wrapper.calls += 1
        return func(*args, **kwargs)

    return wrapper


def memo(func: Callable) -> Callable:
    """
    Memoize a function so that it caches all return values for
    faster future lookups.
    """

    cache = {}

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Проверим есть ли готовый результат в кеше
        existing_result: Any = cache.get(args)
        if existing_result is not None:
            # Если есть - вернем результат
            return existing_result
        # Если нет - сохраним в кеш и запустим функцию
        result = func(*args, **kwargs)
        cache[args] = result
        return result

    return wrapper


def n_ary(func: Callable) -> Callable:
    """
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    """

    @wraps(func)
    def wrapper(x, *args):
        return x if not args else func(x, wrapper(*args))

    return wrapper


def trace(string_indent: str) -> Callable:
    """
    Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3
    """

    def deco(func: Callable) -> Callable:
        stack_lvl = 0

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal stack_lvl
            func_name = func.__name__
            _args = (repr(el) for el in args)
            args_str = ', '.join(_args)
            indent = string_indent * stack_lvl
            print(f"{indent} --> {func_name}({args_str})")
            stack_lvl += 1
            result = func(*args, **kwargs)
            print(f"{indent} <-- {func_name}({args_str}) == {result}")
            stack_lvl -= 1
            return result

        return wrapper

    return deco


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("____")
@memo
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n - 1) + fib(n - 2)


def main():
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(4, 3))
    print("foo was called", foo.calls, "times")

    print(bar(4, 3))
    print(bar(4, 3, 2))
    print(bar(4, 3, 2, 1))
    print("bar was called", bar.calls, "times")

    print(fib.__doc__)
    fib(3)
    print(fib.calls, 'calls made')


if __name__ == '__main__':
    main()

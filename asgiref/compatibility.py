import inspect
import sys

from .sync import iscoroutinefunction
from .typing import (
    ASGI2Application,
    ASGI3Application,
    ASGIApplication,
    ASGIReceiveCallable,
    ASGISendCallable,
    Scope,
)

if sys.version_info >= (3, 10):
    from typing import TypeGuard
else:
    from typing_extensions import TypeGuard


def is_double_callable(application: ASGIApplication) -> TypeGuard[ASGI2Application]:
    """
    Tests to see if an application is a legacy-style (double-callable) application.
    """
    # Look for a hint on the object first
    if getattr(application, "_asgi_single_callable", False):
        return False
    if getattr(application, "_asgi_double_callable", False):
        return True
    # Uninstanted classes are double-callable
    if inspect.isclass(application):
        return True
    # Instanted classes depend on their __call__
    if hasattr(application, "__call__"):
        # We only check to see if its __call__ is a coroutine function -
        # if it's not, it still might be a coroutine function itself.
        if iscoroutinefunction(application.__call__):
            return False
    # Non-classes we just check directly
    return not iscoroutinefunction(application)


def is_single_callable(application: ASGIApplication) -> TypeGuard[ASGI3Application]:
    """
    Tests to see if an application is a new-style (single-callable) application.
    """
    return not is_double_callable(application)


def double_to_single_callable(application: ASGI2Application) -> ASGI3Application:
    """
    Transforms a double-callable ASGI application into a single-callable one.
    """

    async def new_application(
        scope: Scope,
        receive: ASGIReceiveCallable,
        send: ASGISendCallable,
    ) -> None:
        instance = application(scope)
        await instance(receive, send)

    return new_application


def guarantee_single_callable(application: ASGIApplication) -> ASGI3Application:
    """
    Takes either a single- or double-callable application and always returns it
    in single-callable style. Use this to add backwards compatibility for ASGI
    2.0 applications to your server/test harness/etc.
    """
    if is_single_callable(application):
        return application
    elif is_double_callable(application):
        return double_to_single_callable(application)
    raise ValueError("Neither a single nor a double callable was provided")

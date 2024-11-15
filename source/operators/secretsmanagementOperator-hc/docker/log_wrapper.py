import logging
import traceback
import inspect


def tostr(value):
    return "" if value is None else str(value)


class LogWrapper:
    """Helper class to standardize logging output.

    * logger: name of logger or instance of logging.logger
    * logLevel (Number): The level to log e.g. logging.INFO
    * functionName (String): The name of the function calling the logWrapper
    * handlerName (String): The name of the handler calling the logWrapper
    * resourceName (String): The name of the resource being logged
    * componentName (String): The name of the component being logged
    * subject (String): The subject of the log message
    * message (String | Object): The message / object to be logged
                                 - can contain relevant data
    """

    _default_logger = None

    @classmethod
    def set_defaultLogger(cls, d_logger):
        cls._default_logger = d_logger

    @classmethod
    def get_defaultLogger(cls):
        return cls._default_logger

    def __init__(
        self,
        logger=None,
        function_name=None,
        handler_name=None,
        resource_name=None,
        component_name=None,
    ):
        if logger is None:
            if self._default_logger is None:
                logger = ""
            else:
                logger = self._default_logger
        if isinstance(logger, str):
            self.logger = logging.getLogger(logger)
        else:
            self.logger = logger
        self.function_name = function_name
        self.handler_name = handler_name
        self.resource_name = resource_name
        self.component_name = component_name

    def childLogger(
        self,
        logger=None,
        function_name=None,
        handler_name=None,
        resource_name=None,
        component_name=None,
    ):
        child_logger = logger if logger is not None else self.logger
        child_function_name = (
            function_name if function_name is not None else self.function_name
        )
        child_handler_name = (
            handler_name if handler_name is not None else self.handler_name
        )
        child_resource_name = (
            resource_name if resource_name is not None else self.resource_name
        )
        child_component_name = (
            component_name if component_name is not None else self.component_name
        )
        return LogWrapper(
            child_logger,
            child_function_name,
            child_handler_name,
            child_resource_name,
            child_component_name,
        )

    def set(
        self,
        function_name=None,
        handler_name=None,
        resource_name=None,
        component_name=None,
    ):
        self.function_name = (
            function_name if function_name is not None else self.function_name
        )
        self.handler_name = (
            handler_name if handler_name is not None else self.handler_name
        )
        self.resource_name = (
            resource_name if resource_name is not None else self.resource_name
        )
        self.component_name = (
            component_name if component_name is not None else self.component_name
        )

    def debugInfo(self, info_message, debug_info):
        self.info(info_message)
        self.debug(info_message, debug_info)

    def debug(self, subject, message=None):
        self.log(logging.INFO, subject, message)

    def info(self, subject, message=None):
        self.log(logging.INFO, subject, message)

    def error(self, subject, message=None):
        self.log(logging.ERROR, subject, message)

    def exception(self, subject, ex):
        self.error(subject, f"{ex}: {traceback.format_exc()}")

    def log(self, logLevel, subject, message_or_object):
        """Helper function to standardize logging output.

        Args:
            * logLevel (Number): The level to log e.g. logging.INFO
            * subject (String): The subject of the log message
            * message (String | Object): The message / object to be logged - can contain relevant data

        Returns:
            No return value.
        """
        if self.logger.isEnabledFor(logLevel):
            cn = tostr(self.component_name)
            hn = tostr(self.handler_name)
            fn = tostr(self.function_name)
            sub = tostr(subject)
            moo = tostr(message_or_object)
            self.logger.log(
                logLevel,
                f"[{cn}|{tostr(self.resource_name)}|{hn}|{fn}] {sub}: {moo}",
            )
        return


def create_child_log(logw: LogWrapper, func_name, lw_kwargs):
    if "function_name" not in lw_kwargs:
        lw_kwargs["function_name"] = func_name
    if logw is None:
        return LogWrapper(**lw_kwargs)
    if isinstance(logw, str):
        return LogWrapper(**lw_kwargs)
    return logw.childLogger(**lw_kwargs)


def inject_logw_args(func, args, kwargs, lw_kwargs):
    func_name = func.__name__
    arg_names = inspect.getfullargspec(func).args
    if "logw" in arg_names:
        logw_idx = arg_names.index("logw")
        if len(args) > logw_idx:
            logw = args[logw_idx]
            args2 = list(args)
            args2[logw_idx] = create_child_log(logw, func_name, lw_kwargs)
            args = tuple(args2)
        else:
            if "logw" in kwargs:
                logw = kwargs["logw"]
            else:
                logw = None
            kwargs["logw"] = create_child_log(logw, func_name, lw_kwargs)
    return (args, kwargs)


def logwrapper(*lw_args, **lw_kwargs):
    if len(lw_args) == 1 and len(lw_kwargs) == 0 and callable(lw_args[0]):
        # called as @decorator
        def inject_logw(*args, **kwargs):
            func = lw_args[0]
            (args, kwargs) = inject_logw_args(func, args, kwargs, {})
            result = func(*args, **kwargs)
            return result

        return inject_logw

    else:
        # called as @decorator(*args, **kwargs)
        def outer_inject_logw(func):
            def inject_logw(*args, **kwargs):
                (args, kwargs) = inject_logw_args(func, args, kwargs, lw_kwargs)
                result = func(*args, **kwargs)
                return result

            return inject_logw

        return outer_inject_logw

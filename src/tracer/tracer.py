import inspect
import io
import json
from datetime import UTC, datetime, timedelta
from types import FrameType
from typing import Generic, Literal, TypeVar, cast

import rich
from result import Err

T = TypeVar("T")


class TraceBuilder:
    """Builds a trace for a single function call."""

    _func_name: str
    _attributes: dict[str, object]
    _child_traces: "list[Trace[object]]"
    _start_time: datetime
    _end_time: datetime

    def __init__(self, attributes: dict[str, object] | None = None):
        """Initializes the trace builder.

        Args:
            attributes: The initial attributes of the ``TraceBuilder``.
        """
        if attributes is None:
            self._attributes = {}
        else:
            self._attributes = attributes

        self._child_traces = []
        self._start_time = datetime.now(tz=UTC)
        self._end_time = datetime.now(tz=UTC)

        self._func_name = get_function_name()

    def log(self, trace: "Trace[T]") -> T:
        """Captures a trace and returns its enclosed value.

        Args:
            trace (Trace[T]): The trace object to log

        Returns:
            T: The enclosed value from the trace
        """
        self._child_traces.append(
            cast(Trace[object], trace)
        )  # disregard the type of the trace
        return trace.value

    def bind(self, value: T) -> "Trace[T]":
        """Binds a ``value`` to a new ``Trace`` object.

        If the ``value`` is a result.Err[T], the status
        of the trace will be set to "ERROR" instead of "OK".

        Args:
            value (T): The value to return

        Returns:
            Trace[T]: A new trace object
        """
        self._end_time = datetime.now(tz=UTC)
        return Trace(self, value)

    def set_attribute(self, key: str, value: object) -> None:
        """Sets an attribute.

        Use this for logging purposes only, not as an arbitrary
        key-value store for return values.

        Args:
            key: The name of the attribute
            value: The value of the attribute
        """
        self._attributes[key] = value

    def __repr__(self) -> str:
        return pretty_format(
            {
                "start_time": str(self._start_time),
                "end_time": str(self._end_time),
                "attributes": self._attributes,
                "child_traces": self._child_traces,
            },
        )


class Trace(Generic[T]):
    """Represents the metadata surrounding a single operation (or a function call)."""

    _trace_builder: TraceBuilder
    _return_value: T
    _duration: timedelta
    _status: Literal["OK", "ERROR"]

    def __init__(self, trace_builder: TraceBuilder, return_value: T):
        """Creates a ``Trace`` object. This should only ever be called by ``TraceBuilder.bind()``.

        Args:
            trace_builder: A trace builder to log its contents.
            return_value (T): A return value from a function.
        """
        self._trace_builder = trace_builder
        self._return_value = return_value
        self._duration = trace_builder._end_time - trace_builder._start_time  # type: ignore

        if isinstance(return_value, Err):
            self._status = "ERROR"
        else:
            self._status = "OK"

    def __repr__(self) -> str:
        return pretty_format(self.dict())

    def dict(self) -> dict[str, object]:
        """Returns the dictionary representation of the trace.

        Only rely on this for logging purposes.
        """
        duration_seconds = (
            f"{(self._duration / timedelta(milliseconds=1)) / 1000:.2f} seconds"
        )
        return {
            "function_name": self._trace_builder._func_name,  # type: ignore
            "status": self._status,
            "start_time": str(self._trace_builder._start_time),  # type: ignore
            "end_time": str(self._trace_builder._end_time),  # type: ignore
            "duration": duration_seconds,
            "attributes": self._trace_builder._attributes,  # type: ignore
            "return_value": self._return_value,
            "children": self._trace_builder._child_traces,  # type: ignore
        }

    def json(self) -> str:
        """Returns the JSON representation of the trace."""
        return json.dumps(self.dict(), default=safe_serialize, indent=2)

    @property
    def value(self) -> T:
        """The return value enclosed in the trace."""
        return self._return_value


def safe_serialize(object: object) -> object:
    """Safely serialize an object for ``Trace.json()``.

    Args:
        object: The object to serialize
    Returns:
        A JSON-serializable value
    """
    if isinstance(object, Trace):
        return object.dict()

    dunder_dict = getattr(object, "__dict__", None)
    if dunder_dict is not None:
        return dunder_dict

    return repr(object)


def pretty_format(object: object) -> str:
    stream = io.StringIO()
    rich.print(object, file=stream)
    return stream.getvalue()


def get_function_name() -> str:
    """Attempts to retrieve the calling function name, or an empty string if not found."""
    current_frame = inspect.currentframe()

    if current_frame is None:
        return "<N/A>"

    # The calling function of TraceBuilder.__init__() is two frames above
    # so we need to go up the stack twice
    for _ in range(2):
        match current_frame.f_back:
            case None:
                return "<N/A>"
            case FrameType():
                current_frame = current_frame.f_back

    function_name = inspect.getframeinfo(current_frame).function

    self_object = current_frame.f_locals.get("self", None)
    if self_object is not None:
        class_name = self_object.__class__.__name__
        return f"{class_name}.{function_name}"

    cls_object = current_frame.f_locals.get("cls", None)
    if cls_object is not None:
        class_name = cls_object.__name__
        return f"{class_name}.{function_name}"

    return function_name

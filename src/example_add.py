from tracer import Trace, TraceBuilder


def add(a: int, b: int) -> Trace[int]:
    tb = TraceBuilder(
        {
            "arg.a": a,
            "arg.b": b,
        }
    )
    return tb.bind(a + b)


def main() -> Trace[None]:
    tb = TraceBuilder()
    first_number = 3
    second_number = 5

    sum: int = tb.log(add(first_number, second_number))

    print(sum)  # prints: 8

    return tb.bind(None)


if __name__ == "__main__":
    trace = main()
    print(trace.json())

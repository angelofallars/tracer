import random
import time
from dataclasses import dataclass

from result import Err, Ok, Result
from tracer import Trace, TraceBuilder


@dataclass()
class Item:
    id: str
    name: str
    price: int


def process_request() -> Trace[Result[str, str]]:
    tb = TraceBuilder()

    item_result = tb.log(get_item("seUfO284e"))
    match item_result:
        case Err(err):
            return tb.bind(Err(err))
        case Ok(item):
            item = item

    return tb.bind(Ok(item.name))


def get_item(id: str) -> Trace[Result[Item, str]]:
    tb = TraceBuilder({"id": id})

    # simulate DB request delay
    time.sleep(1.25)

    # simulate DB failure
    if random.choice((True, False)):
        return tb.bind(Err(f"Item with id '{id}' not found"))
    else:
        return tb.bind(Ok(Item(id=id, name="Salt Shaker", price=24)))


if __name__ == "__main__":
    trace = process_request()
    trace.json()
    print(trace.json())

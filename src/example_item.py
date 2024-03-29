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


def process_request() -> Trace[Result[None, str]]:
    tb = TraceBuilder()

    get_item_result = tb.log(get_item("seUfO284e"))
    match get_item_result:
        case Err(err):
            return tb.bind(Err(err))
        case Ok(item):
            item = item

    item.name = "Black Salt Shaker"

    update_item_result = tb.log(update_item(item))
    match update_item_result:
        case Err(err):
            return tb.bind(Err(err))
        case Ok(_):
            ...

    return tb.bind(Ok(None))


def get_item(id: str) -> Trace[Result[Item, str]]:
    tb = TraceBuilder({"arg.id": id})

    # simulate DB request delay
    time.sleep(1.25)

    # simulate DB failure
    if random.choice((True, False)):
        return tb.bind(Err(f"Item with id '{id}' not found"))
    else:
        return tb.bind(Ok(Item(id=id, name="Salt Shaker", price=24)))


def update_item(item: Item) -> Trace[Result[None, str]]:
    tb = TraceBuilder({"arg.item": item})

    # simulate DB request delay
    time.sleep(0.75)

    if random.choice((True, False)):
        return tb.bind(Err("Error updating item with id '{item.id}'"))
    else:
        return tb.bind(Ok(None))


if __name__ == "__main__":
    trace = process_request()
    print(trace.json())

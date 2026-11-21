"""Lịch đặt trước được công bố một lần cho mỗi Ngày hoặc ca quán độc lập."""

from ..ids import sort_by_id


def schedule(tuning, scenario, streams, dishes):
    config = tuning.get("reservations")
    if config is None:
        return []
    if "reservations" in scenario:
        return [dict(order, state="scheduled") for order in sort_by_id(scenario["reservations"])]
    if not scenario.get("random_reservations", True):
        return []
    rng = streams.get("reservations")
    tables = [table["id"] for table in sort_by_id(tuning["quan"]["tables"])]
    menu = sorted(dishes)
    first_tick = round(config["table_hold_s"] * tuning["tick_hz"])
    last_tick = round(tuning["quan"]["duration_s"] * tuning["tick_hz"]) - 1
    return [
        {"id": f"R{i}", "table_id": table, "dish_id": rng.choice(menu),
         "arrival_tick": rng.randint(first_tick, last_tick), "state": "scheduled"}
        for i, table in enumerate(rng.sample(tables, config["count"]), 1)
    ]


def announcements(orders, phase):
    return [
        ("reservation_announced", {"reservation_id": order["id"], "table_id": order["table_id"],
                                   "dish_id": order["dish_id"], "arrival_tick": order["arrival_tick"]}, phase)
        for order in orders
    ]

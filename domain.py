"""Paired random experiments with bounded prices and explicit demand assumptions."""
import math
import uuid

import numpy as np

from platform_core import Store, now


def simulate(config):
    if config["cost"] >= config["base_price"]:
        raise ValueError("Unit cost must be below the base price.")
    rng = np.random.default_rng(config["seed"])
    # Common random numbers make strategy comparisons paired and reproducible.
    potential = rng.poisson(config["daily_demand"], size=(config["trials"], config["days"]))
    uniforms = rng.random((config["trials"], config["days"], 1000))
    strategies = {}
    for strategy in ("Fixed price", "Competitor match", "Inventory aware"):
        totals, daily_profit, daily_price, daily_stock = [], [], [], []
        for trial in range(config["trials"]):
            stock, revenue, profit, sold = config["stock"], 0.0, 0.0, 0
            trial_profit, trial_price, trial_stock = [], [], []
            for day in range(config["days"]):
                if strategy == "Fixed price":
                    price = config["base_price"]
                elif strategy == "Competitor match":
                    price = config["competitor_price"] * .99
                else:
                    target_stock = config["stock"] * (1 - day / config["days"])
                    pressure = (target_stock - stock) / max(1, config["stock"])
                    price = config["base_price"] * (1 + pressure * .65)
                price = round(max(config["cost"] * 1.05, min(config["base_price"] * 1.4, max(config["base_price"] * .65, price))), 2)
                # Purchase probability is an explicit assumed demand curve, not a learned forecast.
                exponent = max(-40, min(40, config["elasticity"] * (price / config["competitor_price"] - 1)))
                conversion = 1 / (1 + math.exp(exponent))
                arrivals = min(1000, int(potential[trial, day]))
                quantity = min(stock, int(np.sum(uniforms[trial, day, :arrivals] < conversion)))
                stock -= quantity
                revenue += quantity * price
                day_profit = quantity * (price - config["cost"])
                profit += day_profit
                sold += quantity
                trial_profit.append(day_profit); trial_price.append(price); trial_stock.append(stock)
            # Unsold stock is valued at cost, not treated as a fabricated operating loss.
            totals.append(dict(revenue=revenue, profit=profit, units=sold, remaining=stock))
            daily_profit.append(trial_profit); daily_price.append(trial_price); daily_stock.append(trial_stock)
        profits = [r["profit"] for r in totals]
        strategies[strategy] = dict(
            revenue=float(np.mean([r["revenue"] for r in totals])), profit=float(np.mean(profits)),
            profit_p10=float(np.quantile(profits, .1)), profit_p90=float(np.quantile(profits, .9)),
            units=float(np.mean([r["units"] for r in totals])), remaining=float(np.mean([r["remaining"] for r in totals])),
            daily_profit=np.mean(daily_profit, axis=0).tolist(), daily_price=np.mean(daily_price, axis=0).tolist(),
            daily_stock=np.mean(daily_stock, axis=0).tolist())
    best = max(strategies, key=lambda k: strategies[k]["profit"])
    return dict(id=str(uuid.uuid4()), created=now(), config=config, strategies=strategies, best=best,
                assumptions="Poisson arrivals; logistic price response; no replenishment, taxes, returns or advertising costs. Synthetic simulation, not a business forecast.")


class Experiments:
    def __init__(self, root):
        self.store = Store(root)

    def run(self, config):
        result = simulate(config)
        history = self.store.get("experiments", [])
        self.store.put("experiments", [result] + history[:39])
        self.store.audit("Experiment completed", {"id": result["id"], "seed": config["seed"], "best": result["best"]})
        return result

    def history(self):
        return self.store.get("experiments", [])

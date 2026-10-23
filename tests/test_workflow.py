DEFAULT = dict(name="Deterministic trial", base_price=60, cost=25, competitor_price=58,
               stock=300, days=10, daily_demand=40, elasticity=3, trials=10, seed=42)


def test_simulation_reproducible_bounded_and_stock_conserving(workspace):
    c = workspace.client
    a = c.post("/api/experiments", json=DEFAULT).json()
    b = c.post("/api/experiments", json=DEFAULT).json()
    assert a["strategies"] == b["strategies"]
    for s in a["strategies"].values():
        assert abs(s["units"] + s["remaining"] - DEFAULT["stock"]) < 1e-8
        assert all(s["daily_stock"][i] >= s["daily_stock"][i+1] for i in range(9))
        assert all(39 <= p <= 84 for p in s["daily_price"])
        assert s["profit_p10"] <= s["profit_p90"]
    assert len(c.get("/api/experiments").json()) == 2
    assert c.get("/api/experiments/" + a["id"]).json()["id"] == a["id"]


def test_invalid_cost_and_nonfinite_input_rejected(workspace):
    c = workspace.client
    assert c.post("/api/experiments", json={**DEFAULT, "cost": 90}).status_code == 400
    assert c.post("/api/experiments", json={**DEFAULT, "days": 0}).status_code == 422
    assert c.post("/api/experiments", json={**DEFAULT, "trials": 100000}).status_code == 422
    assert c.get("/api/experiments").json() == []

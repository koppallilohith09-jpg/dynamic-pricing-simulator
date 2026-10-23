from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from platform_core import create_app
from domain import Experiments

ROOT = Path(__file__).parent
engine = Experiments(ROOT)
app = create_app(ROOT, "Margin")


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    name: str = Field(default="Untitled experiment", min_length=1, max_length=80)
    base_price: float = Field(default=60, gt=0, le=100000)
    cost: float = Field(default=25, ge=0, le=100000)
    competitor_price: float = Field(default=58, gt=0, le=100000)
    stock: int = Field(default=600, ge=1, le=100000)
    days: int = Field(default=30, ge=3, le=90)
    daily_demand: float = Field(default=40, ge=1, le=500)
    elasticity: float = Field(default=3, ge=.1, le=12)
    trials: int = Field(default=40, ge=5, le=100)
    seed: int = Field(default=42, ge=0, le=2147483647)


@app.post("/api/experiments")
def run(body: Configuration):
    return engine.run(body.model_dump())


@app.get("/api/experiments")
def history():
    return engine.history()


@app.get("/api/experiments/{experiment_id}")
def detail(experiment_id: str):
    item = next((r for r in engine.history() if r["id"] == experiment_id), None)
    if not item:
        raise ValueError("Experiment not found.")
    return item

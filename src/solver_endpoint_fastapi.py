from fastapi import FastAPI
from pydantic import BaseModel

from src.solver_core import TSP


class InputData(BaseModel):
    coords: list


app = FastAPI()


@app.post("/solve")
async def solve(input_data: InputData):
    return TSP(coords=input_data.coords).solve()

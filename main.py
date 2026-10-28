import asyncio
from time import perf_counter

from fastapi import FastAPI
from pydantic import BaseModel, model_validator

app = FastAPI()


class CalculateRequest(BaseModel):
    numbers: list[float]
    delays: list[float]

    @model_validator(mode="after")
    def validate_data(self):
        if len(self.numbers) != len(self.delays):
            raise ValueError("numbers и delays должны быть одинаковой длины")
        if any(delay < 0 for delay in self.delays):
            raise ValueError("Задержки не могут быть отрицательными")
        return self


class Result(BaseModel):
    number: float
    square: float
    delay: float
    time: float


class CalculateResponse(BaseModel):
    results: list[Result]
    total_time: float
    parallel_faster_than_sequential: bool


async def calculate_one(number: float, delay: float) -> Result:
    start = perf_counter()
    await asyncio.sleep(delay)
    return Result(
        number=number,
        square=number ** 2,
        delay=delay,
        time=round(perf_counter() - start, 2),
    )


@app.post("/calculate/", response_model=CalculateResponse)
async def calculate(request: CalculateRequest):
    start = perf_counter()
    results = await asyncio.gather(
        *(
            calculate_one(number, delay)
            for number, delay in zip(request.numbers, request.delays)
        )
    )
    total_time = perf_counter() - start

    start = perf_counter()
    for delay in request.delays:
        await asyncio.sleep(delay)
    sequential_time = perf_counter() - start

    return CalculateResponse(
        results=results,
        total_time=round(total_time, 2),
        parallel_faster_than_sequential=total_time < sequential_time,
    )
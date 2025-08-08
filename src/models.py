from typing import List
from pydantic import BaseModel, field_validator


class Category(BaseModel):
    id: int
    name: str
    direct: bool
    link_url: str
    image_url: str


class Attributes(BaseModel):
    rating: List[str]
    vendorcode: List[str]
    reviewscount: List[str]

    @field_validator('rating')
    def check_rating(cls, v):
        for item in v:
            try:
                val = float(item)
                if not (0 <= val <= 100):
                    raise ValueError()
            except Exception:
                raise ValueError()
        return v

    @field_validator('reviewscount')
    def check_reviewscount(cls, v):
        for item in v:
            if not item.isdigit():
                raise ValueError()
        return v


class ResultItem(BaseModel):
    id: str
    available: bool
    name: str
    brand: str
    price: float
    score: float
    categories: List[Category]
    attributes: Attributes
    link_url: str
    image_url: str
    image_urls: List[str]

    @field_validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Сумма должна быть положительной")
        return v

    @field_validator('score')
    def score_in_range(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("Рейтинг должен быть в диапазоне от 0 до 100")
        return v


class ResponseModel(BaseModel):
    results: List[ResultItem]

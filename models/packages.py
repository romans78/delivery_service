from enum import Enum

from pydantic import BaseModel, Field, field_validator


class PackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    weight: float = Field(..., gt=0, le=1000, description='Вес в кг')
    type: str = Field(..., min_length=1, max_length=200, description='Тип посылки')
    content_value_usd: float = Field(..., gt=0, le=1000000, description='Стоимость в долларах')

    @field_validator('content_value_usd')
    def round_content_value(cls, v):
        return round(v, 2)


class PackageCreate(PackageBase):
    pass


class PackageId(BaseModel):
    id: int = Field(..., description='id типа посылки')


class PackageType(BaseModel):
    id: int = Field(..., description='id типа посылки')
    type_name: str = Field(..., min_length=1, max_length=200, description='Тип посылки')


class PackageInfo(PackageBase):
    delivery_cost: float | str | None = Field(..., description='Стоимость доставки в рублях')

    @field_validator('delivery_cost')
    def validate_delivery_cost(cls, v):
        if v is None or type(v) is str:
            return v
        if 0 < v < 100000000:
            return v
        else:
            raise ValueError('Delivery cost should be greater than 0 and less than 100000000')

    @field_validator('delivery_cost')
    def round_content_value(cls, v):
        if v is None or type(v) is str:
            return v
        return round(v, 2)


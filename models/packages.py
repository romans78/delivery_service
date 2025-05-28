from enum import Enum

from pydantic import BaseModel, Field, field_validator


class PackageType(str, Enum):
    clothes = 'одежда'
    electronics = 'электроника'
    other = 'разное'


class PackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    weight: float = Field(..., gt=0, le=1000, description='Вес в кг')
    type: PackageType = Field(..., description='Тип посылки')
    content_value_usd: float = Field(..., gt=0, le=1000000, description='Стоимость в долларах')

    @field_validator('content_value_usd')
    def round_content_value(cls, v):
        return round(v, 2)

class PackageCreate(PackageBase):
    pass

class PackageId(BaseModel):
    id: str


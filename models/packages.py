from pydantic import BaseModel, Field, field_validator


class PackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    weight: float = Field(..., gt=0, le=1000, description='Weight in kilograms')
    type_name: str = Field(..., description='Package type name')
    content_value_usd: float = Field(..., gt=0, le=1000000, description='Cost in dollars')

    @field_validator('content_value_usd')
    def round_content_value(cls, v):
        return round(v, 2)

    @field_validator('type_name')
    def validate_type_name(cls, v):
        type_names = ['одежда', 'электроника', 'разное']
        if v.lower() not in type_names:
            raise ValueError(f'No such type exists. Type name should be one of these: {", ".join(type_names)}')
        else:
            return v.lower()


class PackageCreate(PackageBase):
    pass


class PackageId(BaseModel):
    id: int = Field(..., description='Package id')


class PackageType(BaseModel):
    id: int = Field(..., description='Package type id')
    type_name: str = Field(..., min_length=1, max_length=200, description='Package type name')


class PackageInfo(PackageBase):
    delivery_cost: float | str | None = Field(..., description='Delivery cost in roubles')
    id: int = Field(..., description='Package id')
    type_id: int = Field(..., description='Package type id')

    @field_validator('delivery_cost')
    def validate_delivery_cost(cls, value):
        if value is None or type(value) is str:
            return value
        if 0 < value < 100000000:
            return value
        else:
            raise ValueError('Delivery cost should be greater than 0 and less than 100000000')

    @field_validator('delivery_cost')
    def round_content_value(cls, value):
        if value is None or type(value) is str:
            return value
        return round(value, 2)


class PackageInfoNoId(PackageBase):
    delivery_cost: float | str | None = Field(..., description='Delivery cost in roubles')

    @field_validator('delivery_cost')
    def validate_delivery_cost(cls, value):
        if value is None or type(value) is str:
            return value
        if 0 < value < 100000000:
            return value
        else:
            raise ValueError('Delivery cost should be greater than 0 and less than 100000000')

    @field_validator('delivery_cost')
    def round_content_value(cls, value):
        if value is None or type(value) is str:
            return value
        return round(value, 2)


class PaginatedPackages(BaseModel):
    data: list[PackageInfo]
    meta: dict

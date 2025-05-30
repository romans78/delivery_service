from .base import Base
from sqlalchemy import Column, Integer, String, Enum, Float


class PackageType(str, Enum):
    clothes = 'одежда'
    electronics = 'электроника'
    other = 'разное'


class Package(Base):
    __tablename__ = 'package'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    content_value_usd = Column(Float, nullable=False)

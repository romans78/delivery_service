from .base import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.dialects.mysql import CHAR


class PackageTypeTable(Base):
    __tablename__ = 'package_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(200), nullable=False)


class PackageTable(Base):
    __tablename__ = 'package'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    weight = Column(Float, nullable=False)
    type_id = Column(Integer, ForeignKey(PackageTypeTable.id), nullable=False)
    content_value_usd = Column(Float, nullable=False)
    session_id = Column(CHAR(36), nullable=False)
    delivery_cost = Column(Float, nullable=True)
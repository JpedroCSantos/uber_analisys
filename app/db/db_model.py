from db.db import Base
from sqlalchemy import Column, DateTime, Float, Integer, Numeric, String
from sqlalchemy.sql import func


class Yellow(Base):
    __tablename__ = "trips"
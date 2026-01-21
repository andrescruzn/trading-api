# app/extensions/db/base.py
# -*- coding: utf-8 -*-

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Base declarativa para todos los modelos SQLAlchemy.
    """
    pass
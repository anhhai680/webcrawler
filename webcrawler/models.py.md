from sqlalchemy import create_engine, Column, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Integer, SmallInteger, String, Date, DateTime, Float, Boolean, Text, JSON, DECIMAL)

from scrapy.utils.project import get_project_settings

DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(get_project_settings().get("CONNECTION_STRING"))


def create_table(engine):
    DeclarativeBase.metadata.create_all(engine)


class EcrawlDB(DeclarativeBase):
    __tablename__ = "craw_products"

    id = Column(Integer, primary_key=True)
    cid = Column('category_id', Integer)
    title = Column('title', String(256))
    description = Column('short_description', String(4000))
    swatchcolors = Column('swatch_colors', JSON)
    specifications = Column('specifications', JSON)
    price = Column('price', DECIMAL)
    images = Column('images', JSON)
    link = Column('link', String(1000))
    #brand = Column('brand', String(256))
    shop = Column('shop', String(150))
    domain = Column('domain_name', String(256))
    #status = Column('status', Boolean)
    #last_update = Column('last_update', DateTime)

# Modules
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime


# Fact Table
class FactData(SQLModel, table=True):
    DateKey: int = Field(primary_key=True, foreign_key="dimdate.DateKey")
    StationKey: int = Field(primary_key=True, foreign_key="dimstation.StationKey")
    ProductKey: int = Field(primary_key=True, foreign_key="dimproduct.ProductKey")
    MomentKey: int = Field(primary_key=True, foreign_key="dimmoment.MomentKey")
    Price: float = Field(..., nullable=False)
    LoadAt: datetime = Field(default=datetime.now(), nullable=False)
    IsReliable: bool = Field(default=True, nullable=False)

    # Relationship
    date: Optional["DimDate"] = Relationship(back_populates="facts")
    station: Optional["DimStation"] = Relationship(back_populates="facts")
    product: Optional["DimProduct"] = Relationship(back_populates="facts")
    moment: Optional["DimMoment"] = Relationship(back_populates="facts")


# Dimension Tables
class DimDate(SQLModel, table=True):
    DateKey: Optional[int] = Field(default=None, primary_key=True)
    DateID: datetime
    CreatedAt: datetime = Field(default=datetime.now())
    EndOfUse: Optional[datetime] = Field(default=None)

    # Relationship
    facts: list[FactData] = Relationship(back_populates="date")


class DimStation(SQLModel, table=True):
    StationKey: Optional[int] = Field(default=None, primary_key=True)
    StationID: int
    StationName: str = Field(max_length=512)
    StationAddress: Optional[str] = Field(max_length=512)
    StationPostalCode: str = Field(max_length=5)
    StationLatitude: float
    StationLongitude: float
    StationLocation: str = Field(max_length=512)
    StationMunicipality: str = Field(max_length=512)
    StationMunicipalityID: int
    StationProvince: str = Field(max_length=512)
    StationProvinceID: int
    StationAC: str = Field(max_length=512)
    StationACID: int
    StationIsland: str = Field(max_length=512)
    StationIslandID: int
    CreatedAt: datetime = Field(default=datetime.now())
    EndOfUse: Optional[datetime] = None

    # Relationship
    facts: list[FactData] = Relationship(back_populates="station")


class DimProduct(SQLModel, table=True):
    ProductKey: Optional[int] = Field(default=None, primary_key=True)
    ProductID: str = Field(max_length=64)
    ProductName: str = Field(max_length=64)
    CreatedAt: datetime = Field(default=datetime.now())
    EndOfUse: Optional[datetime] = None

    # Relationship
    facts: list[FactData] = Relationship(back_populates="product")


class DimMoment(SQLModel, table=True):
    MomentKey: Optional[int] = Field(primary_key=True)
    MomentID: str = Field(max_length=64)
    CreatedAt: datetime = Field(default=datetime.now())
    EndOfUse: Optional[datetime] = None

    # Relationship
    facts: list[FactData] = Relationship(back_populates="moment")

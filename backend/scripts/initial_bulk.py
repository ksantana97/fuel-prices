# Libraries
import pandas as pd
import os

# Modules
from db.models import DimDate, DimProduct, DimMoment, DimStation
from sqlmodel import create_engine, Session
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.logger_config import setup_logger

# Loading env vars
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# Logger configuration for this script
log_path = "logs/initial_bulk.log"
logger = setup_logger("initial_bulk", log_path)

# Engine SQLite creation
engine = create_engine(database_url, echo=True)


# Functions
def massive_load(data):

    with Session(engine) as session:
        session.bulk_save_objects(data)
        session.commit()


def load_dim_date():

    # Generation data
    start_date = datetime(2024, 1, 1)
    date_list = [start_date + timedelta(days=i) for i in range(5000)]
    dates = [DimDate(DateID=date) for date in date_list]

    # Loading data
    massive_load(dates)


def load_dim_product():

    # Generation data
    product_ids = [
        "Precio Biodiesel",
        "Precio Bioetanol",
        "Precio Gas Natural Comprimido",
        "Precio Gas Natural Licuado",
        "Precio Gases licuados del petróleo",
        "Precio Gasoleo A",
        "Precio Gasoleo B",
        "Precio Gasoleo Premium",
        "Precio Gasolina 95 E10",
        "Precio Gasolina 95 E5",
        "Precio Gasolina 95 E5 Premium",
        "Precio Gasolina 98 E10",
        "Precio Gasolina 98 E5",
        "Precio Hidrogeno",
    ]
    product_names = [
        "BIODIÉSEL",
        "BIOETANOL",
        "GNC",
        "GNL",
        "GLP",
        "GASÓLEO A",
        "GASÓLEO B",
        "GASÓLEO PREMIUM",
        "GASOLINA 95 E10",
        "GASOLINA 95 E5",
        "GASOLINA 95 PREMIUM",
        "GASOLINA 98 E10",
        "GASOLINA 98 E5",
        "HIDRÓGENO",
    ]
    products = [
        DimProduct(ProductID=product_ids[n], ProductName=product_names[n])
        for n in range(len(product_names))
    ]

    # Loading data
    massive_load(products)


def load_dim_moment():

    # Generation data
    moments_id = ["Madrugada", "Mañana", "Mediodía", "Tarde", "Noche"]
    moments = [DimMoment(MomentID=moment) for moment in moments_id]

    # Loading data
    massive_load(moments)


def load_dim_station():

    # Baseline data
    can_prices_ren = pd.read_csv("data/init/baseline_master.csv", sep=";")
    print(can_prices_ren.head())
    # Table columns
    dim_station_cols = [
        "StationID",
        "StationName",
        "StationAddress",
        "StationPostalCode",
        "StationLatitude",
        "StationLongitude",
        "StationLocation",
        "StationMunicipality",
        "StationMunicipalityID",
        "StationProvince",
        "StationProvinceID",
        "StationAC",
        "StationACID",
        "StationIsland",
        "StationIslandID"
    ]

    # Renaming some columns
    can_prices_ren = can_prices_ren.rename(
        columns={
            "IDEESS": "StationID",
            "Rótulo": "StationName",
            "Dirección": "StationAddress",
            "C.P.": "StationPostalCode",
            "Latitud": "StationLatitude",
            "Longitud (WGS84)": "StationLongitude",
            "Localidad": "StationLocation",
            "Municipio": "StationMunicipality",
            "IDMunicipio": "StationMunicipalityID",
            "Provincia": "StationProvince",
            "IDProvincia": "StationProvinceID",
            "IDCCAA": "StationACID",
            "Isla": "StationIsland",
            "IdIsla": "StationIslandID"
        }
    )

    # Normalizing columns
    for col_name in ["Latitude", "Longitude"]:
        can_prices_ren[f"Station{col_name}"] = can_prices_ren[
            f"Station{col_name}"
        ].str.replace(",", ".")
    for col_name in [
        "StationName",
        "StationAddress",
        "StationLocation",
        "StationMunicipality",
        "StationProvince",
        "StationIsland"
    ]:
        can_prices_ren[col_name] = can_prices_ren[col_name].str.upper()
    can_prices_ren = can_prices_ren.astype(
        {
            "StationLatitude": "str",
            "StationLongitude": "str",
            "StationPostalCode": "str",
        }
    )

    # Creation of some columns
    can_prices_ren["StationAC"] = "CANARIAS"

    # Selecting relevant columns
    df_dim_station = can_prices_ren[dim_station_cols]

    # Creating objects
    stations = [
        DimStation(
            StationID=row["StationID"],
            StationName=row["StationName"],
            StationAddress=row["StationAddress"],
            StationPostalCode=row["StationPostalCode"],
            StationLatitude=row["StationLatitude"],
            StationLongitude=row["StationLongitude"],
            StationLocation=row["StationLocation"],
            StationMunicipality=row["StationMunicipality"],
            StationMunicipalityID=row["StationMunicipalityID"],
            StationProvince=row["StationProvince"],
            StationProvinceID=row["StationProvinceID"],
            StationAC=row["StationAC"],
            StationACID=row["StationACID"],
            StationIsland=row["StationIsland"],
            StationIslandID=row["StationIslandID"],
        )
        for _, row in df_dim_station.iterrows()
    ]

    # Loading data
    massive_load(stations)


# Summarizing functions to establish a pipeline for load
bulk_funcs = {
    "DimDate": load_dim_date,
    "DimProduct": load_dim_product,
    "DimMoment": load_dim_moment,
    "DimStation": load_dim_station,
}

# Pipeline
logger.info("Initial bulk of dimensions")
for bulk_func in bulk_funcs:

    try:

        bulk_funcs[bulk_func]()
        logger.info(f"{bulk_func} loaded")

    except Exception as e:

        logger.error(f"Error during {bulk_func} bulking: {e}")

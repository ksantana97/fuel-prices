# Libraries
import json
import os
import pandas as pd
import requests
import sqlite3

# Modules
from datetime import datetime
from db.models import FactData
from dotenv import load_dotenv
from sqlmodel import create_engine, Session
from typing import Any, Dict
from utils.logger_config import setup_logger

# Loading environment vars
load_dotenv()
api_link = os.getenv("API_LINK")
database_name = os.getenv("DATABASE_NAME")
database_url = os.getenv("DATABASE_URL")

# Logger configuration for this script
log_path = "logs/daily_task.log"
logger = setup_logger("daily_task", log_path)


# Functions
def ext_mom_id(hour: int) -> str:
    """
    Determines the stage of the day based on the given hour in 24-hour format.

    Args:
        hour (int): Hour in 24-hour format (0-23).

    Returns:
        str: The stage of the day:
             - "Madrugada" for 1-5 hours.
             - "Mañana" for 6-11 hours.
             - "Mediodía" for 12 hours.
             - "Tarde" for 13-19 hours.
             - "Noche" for 20-23 hours.
             - "Madrugada" for 0 hours.
    """
    if 1 <= hour < 6:
        return "Madrugada"
    elif 6 <= hour < 12:
        return "Mañana"
    elif hour == 12:
        return "Mediodía"
    elif 13 <= hour < 20:
        return "Tarde"
    elif 20 <= hour < 24:
        return "Noche"
    else:  # hour == 0
        return "Madrugada"


def ret_key(db: Any, id_col: str, key_col: str, value_to_filter: Any) -> Any:
    """
    Retrieves a value from a specified DataFrame column based on a filter condition.

    Args:
        db (Any): The database or DataFrame object containing the data.
        id_col (str): The name of the column to filter by.
        key_col (str): The name of the column from which to retrieve the value.
        value_to_filter (Any): The value used to filter the `id_col`.

    Returns:
        Any: The first value in the `key_col` matching the filter condition.
    """
    tmp_df = db[db[id_col] == value_to_filter][key_col].tolist()[0]
    return tmp_df


def price_to_float(val: str) -> float:
    """
    Converts a price string with commas into a float.

    Args:
        val (str): The price string with commas as decimal separators (e.g., "1,234").

    Returns:
        float: The price as a float.
    """
    # Replace commas with dots
    val_with_dot = val.replace(",", ".")

    # Convert to float
    val_float = float(val_with_dot)

    return val_float


def read_api_info(api_link: str) -> Dict[str, Any]:
    """
    Fetches data from an API and returns the JSON response.

    Args:
        api_link (str): The URL of the API to fetch data from.

    Returns:
        Dict[str, Any]: The JSON response from the API as a dictionary.

    Raises:
        Exception: If an error occurs during the API request.
    """
    try:
        response = requests.get(api_link)
        print("API data extracted successfully!")
    except Exception as e:
        print("Error during API data extraction!")
        raise e

    response_json = json.loads(response.text)
    return response_json


# Global variables
current_date = datetime.now()

# Retrieving dimensional data from database
try:

    conn = sqlite3.connect(database_name)
    logger.info("Connected to database")

    dimensions = {}
    tables_names = ["dimdate", "dimstation", "dimproduct", "dimmoment"]
    for table_name in tables_names:
        query_table_data = f"SELECT * FROM {table_name};"
        try:
            df = pd.read_sql_query(query_table_data, conn)
            logger.info(f"{table_name} successfully read")
        except Exception as e:
            logger.error(f"Error reading {table_name}: {e}")
        dimensions[table_name] = df

    conn.close()  # Closing connection

except Exception as e:

    logger.error(f"Error during database connection: {e}")

# Retrieving info from API
try:
    response_json = read_api_info(api_link)
    logger.info("Retrieved info from api successfully")

except Exception as e:
    logger.error(f"Error retrieving api info: {e}")

# Generating  date and moment id
date_id = current_date.replace(hour=0, minute=0, second=0, microsecond=0).strftime(
    "%Y-%m-%d %H:%M:%S.%f"
)
moment_id = ext_mom_id(current_date.hour)

# Generating date and moment key
date_key = ret_key(dimensions["dimdate"], "DateID", "DateKey", date_id)
moment_key = ret_key(dimensions["dimmoment"], "MomentID", "MomentKey", moment_id)

# For each station service we create the fact object (fuel prices)
logger.info("Creating facts")
facts = []
for element in response_json["ListaEESSPrecio"]:

    # We only want canary stations
    if element["IDProvincia"] in ["35", "38"]:
        station_id = int(element["IDEESS"])
    else:
        continue

    # Getting facts
    try:

        # Getting StationKey
        station_key = ret_key(
            dimensions["dimstation"], "StationID", "StationKey", station_id
        )

        # Getting ProductKey and single fact
        for row in dimensions["dimproduct"].itertuples():
            if element[row.ProductID] != "":
                fact = FactData(
                    DateKey=date_key,
                    StationKey=station_key,
                    ProductKey=row.ProductKey,
                    MomentKey=moment_key,
                    Price=price_to_float(element[row.ProductID]),
                )
                facts.append(fact)

    except Exception as e:

        logger.info(f"{station_id} is a canary station and it is not in our database")

# Fill data in database
engine = create_engine(database_url, echo=True)

try:

    logger.info("Loading facts in database")
    with Session(engine) as session:
        session.bulk_save_objects(facts)
        session.commit()

except Exception as e:

    logger.error(f"Error loading facts in database: {e}")

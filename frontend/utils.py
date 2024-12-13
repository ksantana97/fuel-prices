# Libraries
import datetime
import pandas as pd
import folium
import os
import sqlite3
import json

# Modules
from folium import CustomIcon
from typing import List

# Utils for map
dict_imgs = {
    "BP": "icons/BP.png",
    "CEPSA": "icons/CEPSA.png",
    "REPSOL": "icons/Repsol.png",
    "SHELL": "icons/SHELL.png",
    "DISA": "icons/DISA.png",
    "OTHER": "icons/OTHER.png",
}


def get_icon(station_name: str) -> CustomIcon:
    """
    Returns a custom icon based on the station name.

    Args:
        station_name (str): The name of the fuel station.

    Returns:
        CustomIcon: A CustomIcon object representing the fuel station's icon.

    """
    if "BP" in station_name:
        icon = CustomIcon(dict_imgs["BP"], icon_size=(15, 15))
    elif "CEPSA" in station_name:
        icon = CustomIcon(dict_imgs["CEPSA"], icon_size=(15, 15))
    elif "REPSOL" in station_name:
        icon = CustomIcon(dict_imgs["REPSOL"], icon_size=(15, 15))
    elif "SHELL" in station_name:
        icon = CustomIcon(dict_imgs["SHELL"], icon_size=(15, 15))
    elif "DISA" in station_name:
        icon = CustomIcon(dict_imgs["DISA"], icon_size=(15, 15))
    else:
        icon = CustomIcon(dict_imgs["OTHER"], icon_size=(15, 15))
    return icon


def create_basis_map(latitude: float, longitude: float, zoom: int) -> folium.Map:
    """
    Creates a base map with a GeoJSON overlay for the Canary Islands.

    Args:
        latitude (float): The latitude for the map's center.
        longitude (float): The longitude for the map's center.
        zoom (int): The initial zoom level of the map.

    Returns:
        folium.Map: A folium map object with the GeoJSON layer added.
    """
    # Load the GeoJSON file
    geojson_path = "municipios.geojson"
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    # Create a folium map centered at the specified coordinates
    m = folium.Map(
        location=[latitude, longitude], zoom_start=zoom, tiles="CartoDB positron"
    )

    # Add the GeoJSON layer with tooltips for municipalities
    folium.GeoJson(
        geojson_data,
        name="Municipios de Canarias",
        tooltip=folium.GeoJsonTooltip(
            fields=["nombre", "isla"], aliases=["Nombre del municipio:", "Isla:"]
        ),  # Mostrar nombre e isla
    ).add_to(m)

    return m


def add_station_map(row: pd.Series, map: folium.Map) -> None:
    """
    Adds a fuel station marker to a folium map.

    Args:
        row (pd.Series): A row from a pandas DataFrame containing station data.
                         Required fields:
                         - "StationName" (str): Name of the station.
                         - "StationLatitude" (float): Latitude of the station.
                         - "StationLongitude" (float): Longitude of the station.
        map (folium.Map): A folium map object to which the marker will be added.

    Returns:
        None: The function modifies the map in-place.
    """
    station_name = row["StationName"]
    iconito = get_icon(station_name)
    folium.Marker(
        location=[row["StationLatitude"], row["StationLongitude"]],
        popup=row["StationName"],  # Información que aparece al hacer clic
        tooltip=row["StationName"],  # Información al pasar el ratón
        icon=iconito,
    ).add_to(map)


# Retrieving data from database
def ext_mom_key(hour: int) -> str:
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
        return 1
    elif 6 <= hour < 12:
        return 2
    elif hour == 12:
        return 3
    elif 13 <= hour < 20:
        return 4
    elif 20 <= hour < 24:
        return 5
    else:  # hour == 0
        return 1


def retrieve_data_app(curr_mom_key: int) -> pd.DataFrame:
    """
    Retrieves fuel station data from the database for the last 7 days.

    Args:
        curr_mom_key (int): The key representing the specific moment to filter data
                            (e.g., time of day or a predefined time category).

    Returns:
        pd.DataFrame: A DataFrame containing the retrieved data, with columns from the
                      joined tables, including station details, product information,
                      and pricing.
    """
    # Searching SQLite database
    archivos_db = [
        archivo for archivo in os.listdir("../backend") if archivo.endswith(".db")
    ]
    db_name = archivos_db[0]

    # Connection to database and querying for retrieving data
    conn = sqlite3.connect(f"../backend/{db_name}")
    query = f"""
    SELECT 
        factdata.DateKey,
        factdata.StationKey,
        factdata.ProductKey,
        factdata.MomentKey,
        factdata.Price,
        dimdate.DateID,
        dimmoment.MomentID,
        dimproduct.ProductID,
        dimproduct.ProductName,
        dimstation.StationID,
        dimstation.StationName,
        dimstation.StationAddress,
        dimstation.StationPostalCode,
        dimstation.StationLatitude,
        dimstation.StationLongitude,
        dimstation.StationLocation,
        dimstation.StationMunicipality,
        dimstation.StationMunicipalityID,
        dimstation.StationProvince,
        dimstation.StationProvinceID,
        dimstation.StationAC,
        dimstation.StationACID,
        dimstation.StationIsland,
        dimstation.StationIslandID
    FROM factdata
    INNER JOIN dimdate ON factdata.DateKey = dimdate.DateKey
    INNER JOIN dimmoment ON factdata.MomentKey = dimmoment.MomentKey
    INNER JOIN dimproduct ON factdata.ProductKey = dimproduct.ProductKey
    INNER JOIN dimstation ON factdata.StationKey = dimstation.StationKey
    WHERE dimdate.DateID >= datetime('now', '-7 days')
    AND factdata.MomentKey = {curr_mom_key};
    """
    data = pd.read_sql_query(query, conn)
    conn.close()  # Closing connection

    return data


# Selecting current info in database
class InfoSelect:
    """
    A class which organizes the information to show in dashboard with current selection.

    Attributes:
        geo_col_map (dict): Maps geographic levels (e.g., 'COMUNIDAD AUTÓNOMA') to corresponding column names in the DataFrame.
        prod_map (dict): Maps product names to lists of product keys for filtering.
        default_df (pd.DataFrame): The original DataFrame containing fuel station data.
        current_df (pd.DataFrame): The filtered DataFrame based on current selections.
        sel_geo_lvl (str): Selected geographic level (e.g., 'COMUNIDAD AUTÓNOMA').
        sel_geo_ent (str): Selected geographic entity (e.g., 'CANARIAS').
        sel_brand (str): Selected fuel station brand (e.g., 'BP').
        sel_prod (str): Selected product (e.g., 'BIODIÉSEL').
    """

    # Class attributes
    geo_col_map = {
        "COMUNIDAD AUTÓNOMA": "StationAC",
        "PROVINCIA": "StationProvince",
        "ISLA": "StationIsland",
        "MUNICIPIO": "StationMunicipality",
    }
    prod_map = {
        "BIODIÉSEL": [1],
        "BIOETANOL": [2],
        "GNC": [3],
        "GNL": [4],
        "GLP": [5],
        "GASÓLEO A": [6],
        "GASÓLEO B": [7],
        "GASÓLEO PREMIUM": [8],
        "GASOLINA 95": [9, 10, 11],
        "GASOLINA 98": [12, 13],
        "HIDRÓGENO": [14],
    }

    def __init__(self, df: pd.DataFrame):
        """
        Initializes the InfoSelect class with the given DataFrame and default selections.

        Args:
            df (pd.DataFrame): The DataFrame containing fuel station data.
        """
        self.default_df = df
        self.current_df = df
        self.sel_geo_lvl = "COMUNIDAD AUTÓNOMA"
        self.sel_geo_ent = "CANARIAS"
        self.sel_brand = "TODAS"
        self.sel_prod = "BIODIÉSEL"

    def get_distinct_geo_ent_lvls(self, sel_geo_lvl: str) -> List[str]:
        """
        Retrieves a sorted list of unique geographic entities at the selected level.

        Args:
            sel_geo_lvl (str): The geographic level to filter by (e.g., 'PROVINCIA').

        Returns:
            sorted_ent_lst (List[str]): A sorted list of unique geographic entities for the selected level.
        """
        self.sel_geo_lvl = sel_geo_lvl
        ent_lst = self.default_df[InfoSelect.geo_col_map[sel_geo_lvl]].unique().tolist()
        sorted_ent_lst = sorted(ent_lst)
        return sorted_ent_lst

    def set_geo_ent(self, sel_ent: str) -> None:
        """
        Sets the selected geographic entity.

        Args:
            sel_ent (str): The selected geographic entity (e.g., 'LAS PALMAS').
        """
        self.sel_geo_ent = sel_ent

    def set_brand(self, sel_brand: str) -> None:
        """
        Sets the selected fuel station brand.

        Args:
            sel_brand (str): The selected fuel station brand (e.g., 'REPSOL').
        """
        self.sel_brand = sel_brand

    def set_prod(self, sel_prod: str) -> None:
        """
        Sets the selected fuel product.

        Args:
            sel_prod (str): The selected fuel product (e.g., 'GASOLINA 95').
        """
        self.sel_prod = sel_prod

    def ref_info(self):
        """
        Filters the data based on the current selections for geographic entity, product, and brand.
        Updates the `current_df` attribute with the filtered data.
        """
        tmp_df = self.default_df.copy()
        geo_cond = tmp_df[InfoSelect.geo_col_map[self.sel_geo_lvl]] == self.sel_geo_ent
        prod_cond = tmp_df["ProductKey"].isin(InfoSelect.prod_map[self.sel_prod])

        if self.sel_brand in ["BP", "CEPSA", "DISA", "REPSOL", "SHELL"]:
            brand_cond = tmp_df["StationName"].str.contains(self.sel_brand, na=False)
        elif self.sel_brand == "OTRAS":
            brand_cond = ~tmp_df["StationName"].str.contains(self.sel_brand, na=False)
        else:
            brand_cond = True

        cond = geo_cond & prod_cond & brand_cond
        self.current_df = tmp_df[cond]

    @staticmethod
    def get_metrics(df: pd.DataFrame) -> None:
        """
        Calculates the maximum, minimum, and mean fuel prices in the given DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to analyze.

        Returns:
            dict: A dictionary with 'max', 'min', and 'mean' fuel prices.
        """
        max_value = df["Price"].max()
        min_value = df["Price"].min()
        mean_value = round(df["Price"].mean(), 3)
        output_dict = {"max": max_value, "min": min_value, "mean": mean_value}
        return output_dict

    @staticmethod
    def get_output_kpis(dict: dict) -> dict:
        """
        Calculates key performance indicators (KPIs) and their deltas.

        Args:
            dict (dict): A dictionary containing today's and previous metrics.

        Returns:
            dict: A dictionary with KPIs and deltas for 'max', 'min', and 'mean' metrics.
        """
        output_dict = {}
        for met_nam in ["max", "min", "mean"]:
            output_dict[met_nam] = {
                "value": dict["tdy"][met_nam],
                "delta": round(dict["tdy"][met_nam] - dict["prev"][met_nam], 3),
            }
        return output_dict

    def get_kpis(self):
        """
        Retrieves KPIs for the current filtered data, comparing today's data with previous days.

        Returns:
            dict: A dictionary with KPIs and deltas for the filtered data.
        """
        max_date_avb = self.current_df["DateKey"].max()
        tdy_df = self.current_df[self.current_df["DateKey"] == max_date_avb]
        prev_df = self.current_df[self.current_df["DateKey"] != max_date_avb]

        prev_metrics = __class__.get_metrics(prev_df)
        tdy_metrics = __class__.get_metrics(tdy_df)

        pre_output_dict = {"prev": prev_metrics, "tdy": tdy_metrics}
        output = __class__.get_output_kpis(pre_output_dict)
        return output

    def get_top_n_cheapest_stat(self, n: int) -> pd.DataFrame:
        """
        Gets the top N cheapest fuel stations based on price for the most recent date.

        Args:
            n (int): The number of cheapest stations to retrieve.

        Returns:
            pd.DataFrame: A DataFrame containing the top N cheapest stations.
        """
        max_date_avb = self.current_df["DateKey"].max()
        tdy_df = self.current_df[self.current_df["DateKey"] == max_date_avb]
        return tdy_df.sort_values(by="Price", ascending=True).head(n)

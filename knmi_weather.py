"""
Simple KNMI weather data fetcher.

Usage:
    from knmi_weather import get_daily, get_hourly
    
    # Just temperature
    df = get_daily()
    
    # With date range
    df = get_daily(start="2023-01-01", end="2024-12-31")
    
    # All columns
    df = get_daily(columns="all")
    
    # Specific station
    df = get_daily(station="260")  # De Bilt
    
    # Average of multiple stations
    df = get_daily(station=["350", "380"], average=True)
    
    # Hourly data
    df = get_hourly(columns=["T", "RH", "U"])

Install from GitHub:
    pip install git+https://github.com/siemhoukes/knmi-weather.git
    
Or direct call:
    import requests
    exec(requests.get("https://raw.githubusercontent.com/siemhoukes/knmi-weather/main/knmi_weather.py").text)

See stations.txt for all available stations.
"""

import io
import requests
import zipfile
import pandas as pd


# Station 350 = Gilze-Rijen (Zuid-Nederland)
DEFAULT_STATION = "350"

# Common stations for quick reference
STATIONS = {
    "de_bilt": "260",
    "schiphol": "240",
    "rotterdam": "344",
    "eindhoven": "370",
    "maastricht": "380",
    "gilze_rijen": "350",
    "groningen": "280",
    "leeuwarden": "270",
    "vlissingen": "310",
    "twenthe": "290",
}

# Available daily columns (most useful ones)
DAILY_COLUMNS = {
    "TG": "temp_avg",      # Daily mean temperature (°C)
    "TN": "temp_min",      # Daily minimum temperature (°C)
    "TX": "temp_max",      # Daily maximum temperature (°C)
    "SQ": "sun_duration",  # Sunshine duration (hours)
    "RH": "precipitation", # Daily precipitation (mm)
    "UG": "humidity",      # Daily mean relative humidity (%)
    "FG": "wind_speed",    # Daily mean wind speed (m/s)
}

# Available hourly columns
HOURLY_COLUMNS = {
    "T": "temp",           # Temperature (°C)
    "TD": "dewpoint",      # Dew point (°C)
    "RH": "precipitation", # Precipitation (mm)
    "U": "humidity",       # Relative humidity (%)
    "FH": "wind_speed",    # Wind speed (m/s)
    "FF": "wind_speed_10m",# Wind speed 10min avg (m/s)
    "Q": "radiation",      # Global radiation (J/cm2)
    "SQ": "sun_duration",  # Sunshine duration (minutes)
    "N": "cloud_cover",    # Cloud cover (oktas)
    "P": "pressure",       # Air pressure (hPa)
}


def _download_zip(url: str, extension: str = ".txt"):
    """Download and extract file from KNMI zip."""
    response = requests.get(url)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        target = [f for f in zf.namelist() if f.endswith(extension)][0]
        return zf.open(target)


def get_daily(
    start: str = None,
    end: str = None,
    station: str | list = DEFAULT_STATION,
    columns: list | str = None,
    average: bool = False,
) -> pd.DataFrame:
    """
    Get daily KNMI weather data.
    
    Args:
        start: Start date (YYYY-MM-DD), default: 2020-01-01
        end: End date (YYYY-MM-DD), default: today
        station: KNMI station number, name, or list of stations
                 Examples: "350", "de_bilt", ["350", "380"]
        columns: List of columns to include, "all", or None for just temp_avg
                 Available: TG, TN, TX, SQ, RH, UG, FG (see DAILY_COLUMNS)
        average: If True and multiple stations given, return average values
    
    Returns:
        DataFrame with date and requested weather columns
    """
    start = start or "2020-01-01"
    end = end or pd.Timestamp.today().strftime("%Y-%m-%d")
    
    # Handle station name lookup
    def resolve_station(s):
        return STATIONS.get(s.lower(), s) if isinstance(s, str) else s
    
    # Handle single or multiple stations
    if isinstance(station, list):
        stations = [resolve_station(s) for s in station]
    else:
        stations = [resolve_station(station)]
    
    # Fetch data for each station
    all_dfs = []
    for stn in stations:
        df = _fetch_daily_station(stn, start, end, columns)
        if len(stations) > 1:
            df["station"] = stn
        all_dfs.append(df)
    
    if len(all_dfs) == 1:
        return all_dfs[0]
    
    # Multiple stations
    combined = pd.concat(all_dfs, ignore_index=True)
    
    if average:
        # Average across stations per date
        numeric_cols = combined.select_dtypes(include="number").columns.tolist()
        if "station" in numeric_cols:
            numeric_cols.remove("station")
        result = combined.groupby("date")[numeric_cols].mean().reset_index()
        return result
    else:
        return combined


def _fetch_daily_station(station: str, start: str, end: str, columns) -> pd.DataFrame:
    """Fetch daily data for a single station."""
    url = f"https://cdn.knmi.nl/knmi/map/page/klimatologie/gegevens/daggegevens/etmgeg_{station}.zip"
    
    try:
        raw_file = _download_zip(url)
    except Exception as e:
        raise ValueError(f"Could not download data for station {station}: {e}")
    
    # Parse data lines (skip comments and headers)
    lines = []
    for line in raw_file:
        line = line.decode("utf-8").strip()
        if line and not line.startswith("#") and line.split(",")[0].strip().isdigit():
            lines.append(line)
    
    # Column names from KNMI daily data
    all_cols = [
        "STN", "YYYYMMDD", "DDVEC", "FHVEC", "FG", "FHX", "FHXH", "FHN", "FHNH",
        "FXX", "FXXH", "TG", "TN", "TNH", "TX", "TXH", "T10N", "T10NH", "SQ", "SP",
        "Q", "DR", "RH", "RHX", "RHXH", "PG", "PX", "PXH", "PN", "PNH", "VVN",
        "VVNH", "VVX", "VVXH", "NG", "UG", "UX", "UXH", "UN", "UNH", "EV24"
    ]
    
    df = pd.read_csv(io.StringIO("\n".join(lines)), header=None, low_memory=False)
    df.columns = all_cols[:len(df.columns)]
    
    # Parse date
    df["date"] = pd.to_datetime(df["YYYYMMDD"].astype(str), format="%Y%m%d")
    df = df[(df["date"] >= start) & (df["date"] <= end)]
    
    # Determine which columns to return
    if columns is None:
        cols_to_get = ["TG"]
    elif columns == "all":
        cols_to_get = list(DAILY_COLUMNS.keys())
    else:
        cols_to_get = columns if isinstance(columns, list) else [columns]
    
    # Build result dataframe
    result = df[["date"]].copy()
    for col in cols_to_get:
        if col in df.columns:
            # Convert from 0.1 units to actual units
            result[DAILY_COLUMNS.get(col, col)] = pd.to_numeric(df[col], errors="coerce") / 10.0
    
    return result.reset_index(drop=True)


def get_hourly(
    start: str = None,
    end: str = None,
    station: str = DEFAULT_STATION,
    columns: list | str = None,
) -> pd.DataFrame:
    """
    Get hourly KNMI weather data.
    
    Args:
        start: Start date (YYYY-MM-DD), default: 2021-01-01
        end: End date (YYYY-MM-DD), default: today
        station: KNMI station number, default: 350 (Gilze-Rijen)
        columns: List of columns to include, "all", or None for just temp
                 Available: T, TD, RH, U, FH, FF, Q, SQ, N, P (see HOURLY_COLUMNS)
    
    Returns:
        DataFrame with datetime and requested weather columns
    """
    start = start or "2021-01-01"
    end = end or pd.Timestamp.today().strftime("%Y-%m-%d")
    
    url = f"https://cdn.knmi.nl/knmi/map/page/klimatologie/gegevens/uurgegevens/uurgeg_{station}_2021-2030.zip"
    raw_file = _download_zip(url, ".txt")
    
    # Parse with header
    lines = []
    header_found = False
    for line in raw_file:
        line = line.decode("utf-8").strip()
        if "STN,YYYYMMDD" in line:
            header_found = True
            lines.append(line)
        elif header_found and line and not line.startswith("#"):
            lines.append(line)
    
    df = pd.read_csv(io.StringIO("\n".join(lines)), low_memory=False)
    df.columns = df.columns.str.strip().str.replace("# ", "")
    
    # Create datetime
    df["datetime"] = pd.to_datetime(
        df["YYYYMMDD"].astype(str) + df["HH"].astype(int).astype(str).str.zfill(2),
        format="%Y%m%d%H"
    )
    df = df[(df["datetime"] >= start) & (df["datetime"] <= end)]
    
    # Determine which columns to return
    if columns is None:
        cols_to_get = ["T"]
    elif columns == "all":
        cols_to_get = list(HOURLY_COLUMNS.keys())
    else:
        cols_to_get = columns if isinstance(columns, list) else [columns]
    
    # Build result dataframe
    result = df[["datetime"]].copy()
    for col in cols_to_get:
        if col in df.columns:
            result[HOURLY_COLUMNS.get(col, col)] = pd.to_numeric(df[col], errors="coerce") / 10.0
    
    return result.reset_index(drop=True)


if __name__ == "__main__":
    # Quick test
    print("Daily data:")
    print(get_daily(start="2024-01-01", columns=["TG", "TN", "TX"]).head())
    
    print("\nHourly data:")
    print(get_hourly(start="2024-01-01", columns=["T", "U"]).head())

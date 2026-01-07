# KNMI Weather

Simpele Python module om KNMI weerdata op te halen. Ondersteunt meerdere stations en kan gemiddeldes berekenen.

## Installatie

```bash
pip install git+https://github.com/siemhoukes/knmi-weather.git
```

## Snel gebruiken (zonder installatie)

```python
import requests
exec(requests.get("https://raw.githubusercontent.com/siemhoukes/knmi-weather/main/knmi_weather.py").text)

df = get_daily()
```

## Gebruik

```python
from knmi_weather import get_daily, get_hourly

# Simpelste: alleen gemiddelde temperatuur
df = get_daily()

# Met datum range
df = get_daily(start="2023-01-01", end="2024-12-31")

# Specifiek station (nummer of naam)
df = get_daily(station="260")           # De Bilt
df = get_daily(station="de_bilt")       # Zelfde
df = get_daily(station="eindhoven")     # Eindhoven Airport

# Meerdere stations
df = get_daily(station=["350", "380"])  # Gilze-Rijen + Maastricht

# Gemiddelde van meerdere stations
df = get_daily(station=["350", "380"], average=True)

# Meerdere kolommen
df = get_daily(columns=["TG", "TN", "TX", "RH"])

# Alle beschikbare kolommen
df = get_daily(columns="all")

# Uurlijkse data
df = get_hourly(start="2024-01-01", columns=["T", "U"])
```

## Beschikbare kolommen

### Dagelijks (`get_daily`)

| Code | Output naam | Beschrijving |
|------|-------------|--------------|
| TG | temp_avg | Gemiddelde temperatuur (°C) |
| TN | temp_min | Minimum temperatuur (°C) |
| TX | temp_max | Maximum temperatuur (°C) |
| SQ | sun_duration | Zonneschijnduur (uren) |
| RH | precipitation | Neerslag (mm) |
| UG | humidity | Relatieve luchtvochtigheid (%) |
| FG | wind_speed | Windsnelheid (m/s) |

### Uurlijks (`get_hourly`)

| Code | Output naam | Beschrijving |
|------|-------------|--------------|
| T | temp | Temperatuur (°C) |
| TD | dewpoint | Dauwpunt (°C) |
| RH | precipitation | Neerslag (mm) |
| U | humidity | Relatieve luchtvochtigheid (%) |
| FH | wind_speed | Windsnelheid (m/s) |
| Q | radiation | Globale straling (J/cm²) |
| SQ | sun_duration | Zonneschijnduur (min) |
| N | cloud_cover | Bewolking (octa's) |
| P | pressure | Luchtdruk (hPa) |

## Stations

### Snelle namen

```python
get_daily(station="de_bilt")      # 260
get_daily(station="schiphol")     # 240
get_daily(station="rotterdam")    # 344
get_daily(station="eindhoven")    # 370
get_daily(station="maastricht")   # 380
get_daily(station="gilze_rijen")  # 350 (default)
get_daily(station="groningen")    # 280
get_daily(station="leeuwarden")   # 270
get_daily(station="vlissingen")   # 310
get_daily(station="twenthe")      # 290
```

### Alle stations

Zie `stations.txt` voor de complete lijst met 50+ stations.

Je kunt ook direct het station nummer gebruiken:
```python
get_daily(station="392")  # Horst
get_daily(station="377")  # Ell
```

## Voorbeelden

### Temperatuur voor energie analyse

```python
from knmi_weather import get_daily
import pandas as pd

# Laad energie data
energy = pd.read_csv("energy_usage.csv")
energy["date"] = pd.to_datetime(energy["date"])

# Haal weer op voor dezelfde periode
weather = get_daily(
    start=energy["date"].min().strftime("%Y-%m-%d"),
    end=energy["date"].max().strftime("%Y-%m-%d"),
)

# Merge
df = energy.merge(weather, on="date", how="left")
```

### Gemiddelde van 2 stations (voor locatie tussen stations)

```python
# Bijvoorbeeld voor een locatie tussen Gilze-Rijen en Eindhoven
df = get_daily(
    station=["350", "370"],
    average=True,
    columns=["TG", "TN", "TX"]
)
```

### Vergelijk stations

```python
df = get_daily(
    station=["de_bilt", "maastricht", "groningen"],
    start="2024-01-01"
)

# df bevat nu een 'station' kolom
print(df.groupby("station")["temp_avg"].mean())
```

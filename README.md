# KNMI Weather

Simpele Python module om KNMI weerdata op te halen. Ondersteunt meerdere stations en kan gemiddeldes berekenen.

## Dashboard — weather.siem.codes

Er is een dashboard dat de volledige historie (voor De Bilt vanaf 1901) per station toont: temperatuur, neerslag, zonneschijn, luchtvochtigheid en wind, met datumbereik-presets, automatische aggregatie (dag/week/maand/jaar), stat-tegels, tabelweergave en CSV-export. De selectie staat in de URL, dus elke weergave is deelbaar als link.

- **Code:** [`dashboard/`](dashboard/) (statische pagina, geen dependencies)
- **Data:** [`scripts/build_data.py`](scripts/build_data.py) haalt via deze module de daggegevens op en schrijft compacte JSON per station naar `dashboard/data/`
- **Deploy:** [`.github/workflows/deploy-dashboard.yml`](.github/workflows/deploy-dashboard.yml) bouwt de data dagelijks opnieuw (06:30 UTC) en publiceert naar GitHub Pages

### Eenmalige setup voor weather.siem.codes

1. **GitHub Pages aanzetten:** repo → Settings → Pages → Source: **GitHub Actions**.
2. **DNS:** maak bij je DNS-provider een `CNAME` record aan: `weather.siem.codes` → `siemhoukes.github.io`.
3. **Custom domain:** repo → Settings → Pages → Custom domain: `weather.siem.codes` (en vink "Enforce HTTPS" aan zodra het certificaat is uitgegeven). Het `dashboard/CNAME` bestand wordt al mee-gedeployed.
4. Draai de workflow een keer handmatig (Actions → Deploy dashboard → Run workflow) of push naar `main`.

### Lokaal draaien

```bash
pip install pandas requests
python scripts/build_data.py          # schrijft dashboard/data/
python -m http.server -d dashboard    # open http://localhost:8000
```

Ander station toevoegen? Voeg het toe aan `DASHBOARD_STATIONS` in `scripts/build_data.py` (zie `stations.txt` voor alle stations).

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

"""The one place every table name in the project is written.

A notebook, a dbt profile, an orchestration job and a monitoring query all have
to agree on where a table lives. Writing the name in each of them means a rename
touches every one, and the day a name is wrong in exactly one place is the day a
pipeline writes into a table nobody is reading.

So every name is built here from one catalog constant. Renaming the catalog, or
moving a layer, is one edit in one tested file.

Layers are schemas inside one catalog, and the catalog is per project rather
than per layer: a second project gets its own catalog instead of competing for
`bronze`. In production the same shape would be one catalog per environment -
`energy_dev`, `energy_prod` - holding the same three schemas.
"""

CATALOG = "energy"

BRONZE_SCHEMA = f"{CATALOG}.bronze"
SILVER_SCHEMA = f"{CATALOG}.silver"
GOLD_SCHEMA = f"{CATALOG}.gold"

SCHEMAS = (BRONZE_SCHEMA, SILVER_SCHEMA, GOLD_SCHEMA)

SMARD_RAW = f"{BRONZE_SCHEMA}.smard_raw"
DWD_RAW = f"{BRONZE_SCHEMA}.dwd_raw"

POWER_HOURLY = f"{SILVER_SCHEMA}.power_hourly"
WEATHER_STATION_HOURLY = f"{SILVER_SCHEMA}.weather_station_hourly"
WEATHER_GERMANY_HOURLY = f"{SILVER_SCHEMA}.weather_germany_hourly"

BRONZE_TABLES = (SMARD_RAW, DWD_RAW)
SILVER_TABLES = (POWER_HOURLY, WEATHER_STATION_HOURLY, WEATHER_GERMANY_HOURLY)
ALL_TABLES = BRONZE_TABLES + SILVER_TABLES

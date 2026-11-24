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
`energy_dev`, `energy_prod` - holding the same schemas.

`reference` sits beside the three layers rather than inside them. It holds the
static lookups dbt loads from seed files, which are neither ingested like bronze
nor derived like silver.
"""

CATALOG = "energy"

BRONZE_SCHEMA = f"{CATALOG}.bronze"
SILVER_SCHEMA = f"{CATALOG}.silver"
GOLD_SCHEMA = f"{CATALOG}.gold"

# Static lookups are not a medallion layer: nothing ingests them and nothing
# derives them. They sit in their own schema so bronze, silver and gold keep
# meaning exactly what their comments say.
REFERENCE_SCHEMA = f"{CATALOG}.reference"

SCHEMAS = (BRONZE_SCHEMA, SILVER_SCHEMA, GOLD_SCHEMA, REFERENCE_SCHEMA)

SMARD_RAW = f"{BRONZE_SCHEMA}.smard_raw"
DWD_RAW = f"{BRONZE_SCHEMA}.dwd_raw"

POWER_HOURLY = f"{SILVER_SCHEMA}.power_hourly"
WEATHER_STATION_HOURLY = f"{SILVER_SCHEMA}.weather_station_hourly"
WEATHER_GERMANY_HOURLY = f"{SILVER_SCHEMA}.weather_germany_hourly"

HOURLY_MARKET = f"{GOLD_SCHEMA}.hourly_market"
PRICE_BY_RENEWABLE_QUARTILE = f"{GOLD_SCHEMA}.price_by_renewable_quartile"

SERIES_LOOKUP = f"{REFERENCE_SCHEMA}.series_lookup"
STATION_LOOKUP = f"{REFERENCE_SCHEMA}.station_lookup"

BRONZE_TABLES = (SMARD_RAW, DWD_RAW)
SILVER_TABLES = (POWER_HOURLY, WEATHER_STATION_HOURLY, WEATHER_GERMANY_HOURLY)
GOLD_TABLES = (HOURLY_MARKET, PRICE_BY_RENEWABLE_QUARTILE)
REFERENCE_TABLES = (SERIES_LOOKUP, STATION_LOOKUP)
ALL_TABLES = BRONZE_TABLES + SILVER_TABLES + GOLD_TABLES + REFERENCE_TABLES

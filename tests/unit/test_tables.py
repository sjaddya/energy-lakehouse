"""Unit tests for the table names. They assert shape, not spelling."""

from energy_lakehouse.tables import (
    ALL_TABLES,
    BRONZE_SCHEMA,
    BRONZE_TABLES,
    CATALOG,
    GOLD_SCHEMA,
    SCHEMAS,
    SILVER_SCHEMA,
    SILVER_TABLES,
)

THREE_PART = 3
TWO_PART = 2


def test_every_table_is_a_three_part_name() -> None:
    assert all(len(name.split(".")) == THREE_PART for name in ALL_TABLES)


def test_every_schema_is_a_two_part_name() -> None:
    assert all(len(name.split(".")) == TWO_PART for name in SCHEMAS)


def test_every_name_sits_in_the_one_catalog() -> None:
    for name in (*SCHEMAS, *ALL_TABLES):
        assert name.startswith(f"{CATALOG}.")


def test_the_layers_are_separate_schemas() -> None:
    assert len(set(SCHEMAS)) == len(SCHEMAS)
    assert BRONZE_SCHEMA != SILVER_SCHEMA != GOLD_SCHEMA


def test_each_table_sits_in_the_layer_it_belongs_to() -> None:
    assert all(name.startswith(f"{BRONZE_SCHEMA}.") for name in BRONZE_TABLES)
    assert all(name.startswith(f"{SILVER_SCHEMA}.") for name in SILVER_TABLES)


def test_no_table_name_is_used_twice() -> None:
    assert len(set(ALL_TABLES)) == len(ALL_TABLES)


def test_all_tables_is_every_layer_and_nothing_else() -> None:
    assert set(ALL_TABLES) == set(BRONZE_TABLES) | set(SILVER_TABLES)
    assert len(BRONZE_TABLES) == 2
    assert len(SILVER_TABLES) == 3


def test_gold_has_a_schema_but_no_tables_yet() -> None:
    # a16 adds them. An empty gold schema now is a statement, not an oversight.
    assert GOLD_SCHEMA in SCHEMAS
    assert not [name for name in ALL_TABLES if name.startswith(f"{GOLD_SCHEMA}.")]

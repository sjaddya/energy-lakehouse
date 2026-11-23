{#
    dbt's built-in behaviour is to glue a custom schema onto the target schema,
    so a seed configured with `+schema: reference` would land in
    `silver_reference`. That rule exists so several developers can build into
    one warehouse without colliding; this project has one warehouse and one
    person, and the schema names are the published layer names.

    So a custom schema is used exactly as written, and a model without one falls
    back to the schema in the profile.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}

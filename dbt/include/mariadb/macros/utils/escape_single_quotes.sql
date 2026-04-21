{#
    Default behaviour doubles single quotes for the SQL literal. MariaDB
    behaves identically in default SQL mode, so we mirror the default.
#}
{% macro mariadb__escape_single_quotes(expression) -%}
{{ expression | replace("'", "''") }}
{%- endmacro %}

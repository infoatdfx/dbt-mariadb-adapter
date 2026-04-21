{#
    MariaDB 10.6+ ships no true TRY_CAST. Best portable approximation is
    CONVERT(expr, type) which returns NULL on failure for most numeric and
    temporal types (strings always succeed). This matches the semantics of
    dbt's default__safe_cast for adapters without a real TRY_CAST.
#}
{% macro mariadb__safe_cast(field, type) %}
    convert({{ field }}, {{ type }})
{% endmacro %}

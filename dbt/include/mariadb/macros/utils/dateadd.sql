{#
    MariaDB's DATE_ADD accepts the same interval keywords dbt uses
    (day, week, month, quarter, year, hour, minute, second, microsecond).
#}
{% macro mariadb__dateadd(datepart, interval, from_date_or_timestamp) -%}
    date_add({{ from_date_or_timestamp }}, interval ({{ interval }}) {{ datepart }})
{%- endmacro %}

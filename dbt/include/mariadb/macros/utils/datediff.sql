{#
    MariaDB's TIMESTAMPDIFF handles all the dateparts dbt uses except
    `quarter` (which we map to month/3) and `week` (map to day/7).
    `millisecond` and `microsecond` need explicit scaling.
#}
{% macro mariadb__datediff(first_date, second_date, datepart) -%}
    {%- set dp = datepart|lower -%}
    {%- if dp == 'quarter' -%}
        (timestampdiff(month, {{ first_date }}, {{ second_date }}) div 3)
    {%- elif dp == 'week' -%}
        (timestampdiff(day, {{ first_date }}, {{ second_date }}) div 7)
    {%- elif dp == 'millisecond' -%}
        (timestampdiff(microsecond, {{ first_date }}, {{ second_date }}) div 1000)
    {%- elif dp in ('microsecond', 'second', 'minute', 'hour', 'day', 'month', 'year') -%}
        timestampdiff({{ dp }}, {{ first_date }}, {{ second_date }})
    {%- else -%}
        {{ exceptions.raise_compiler_error(
            "Unsupported datepart for macro datediff in mariadb: " ~ datepart
        ) }}
    {%- endif -%}
{%- endmacro %}

{#
    MariaDB lacks a native date_trunc. Emulate the common dateparts via
    DATE_FORMAT so we return a DATETIME for every level of granularity
    (consistent with postgres/snowflake behaviour).
#}
{% macro mariadb__date_trunc(datepart, date) -%}
    {%- set dp = datepart|lower -%}
    {%- if dp == 'year' -%}
        cast(date_format({{ date }}, '%Y-01-01 00:00:00') as datetime)
    {%- elif dp == 'quarter' -%}
        cast(date_format(
            date_add(
                {{ date }},
                interval -((month({{ date }}) - 1) mod 3) month
            ),
            '%Y-%m-01 00:00:00'
        ) as datetime)
    {%- elif dp == 'month' -%}
        cast(date_format({{ date }}, '%Y-%m-01 00:00:00') as datetime)
    {%- elif dp == 'week' -%}
        {#- ISO week: truncate to Monday -#}
        cast(date_format(
            date_add({{ date }}, interval -(weekday({{ date }})) day),
            '%Y-%m-%d 00:00:00'
        ) as datetime)
    {%- elif dp == 'day' -%}
        cast(date_format({{ date }}, '%Y-%m-%d 00:00:00') as datetime)
    {%- elif dp == 'hour' -%}
        cast(date_format({{ date }}, '%Y-%m-%d %H:00:00') as datetime)
    {%- elif dp == 'minute' -%}
        cast(date_format({{ date }}, '%Y-%m-%d %H:%i:00') as datetime)
    {%- elif dp == 'second' -%}
        cast(date_format({{ date }}, '%Y-%m-%d %H:%i:%s') as datetime)
    {%- else -%}
        {{ exceptions.raise_compiler_error(
            "Unsupported datepart for macro date_trunc in mariadb: " ~ datepart
        ) }}
    {%- endif -%}
{%- endmacro %}

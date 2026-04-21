{#
    MariaDB's LAST_DAY returns the last day of the month. For other dateparts
    we compose it from date_trunc + dateadd of the next period - 1 day.
#}
{% macro mariadb__last_day(date, datepart) -%}
    {%- set dp = datepart|lower -%}
    {%- if dp == 'month' -%}
        cast(last_day({{ date }}) as date)
    {%- elif dp == 'quarter' -%}
        cast(
            date_sub(
                date_add(
                    {{ dbt.date_trunc('quarter', date) }},
                    interval 3 month
                ),
                interval 1 day
            ) as date
        )
    {%- elif dp == 'year' -%}
        cast(
            date_sub(
                date_add(
                    {{ dbt.date_trunc('year', date) }},
                    interval 1 year
                ),
                interval 1 day
            ) as date
        )
    {%- else -%}
        {{ exceptions.raise_compiler_error(
            "Unsupported datepart for macro last_day in mariadb: " ~ datepart
        ) }}
    {%- endif -%}
{%- endmacro %}

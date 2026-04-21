{#
    MariaDB's GROUP_CONCAT is the canonical analogue of listagg.
    `limit_num` is honoured by wrapping in SUBSTRING_INDEX to trim to the first
    N items, since GROUP_CONCAT has no LIMIT clause.
#}
{% macro mariadb__listagg(measure, delimiter_text, order_by_clause, limit_num) -%}
    {%- if limit_num -%}
    substring_index(
        group_concat(
            {{ measure }}
            {% if order_by_clause %} {{ order_by_clause }} {% endif %}
            separator {{ delimiter_text }}
        ),
        {{ delimiter_text }},
        {{ limit_num }}
    )
    {%- else -%}
    group_concat(
        {{ measure }}
        {% if order_by_clause %} {{ order_by_clause }} {% endif %}
        separator {{ delimiter_text }}
    )
    {%- endif -%}
{%- endmacro %}

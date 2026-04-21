{% macro mariadb__any_value(expression) -%}
    any_value({{ expression }})
{%- endmacro %}

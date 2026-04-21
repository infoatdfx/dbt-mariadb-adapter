{#
    MariaDB has no boolean aggregate; coerce to INTEGER (0/1) and use MAX —
    any truthy row lifts the result to 1, which we compare to 1 to get a
    boolean-shaped scalar.
#}
{% macro mariadb__bool_or(expression) -%}
    (max(case when ({{ expression }}) then 1 else 0 end) = 1)
{%- endmacro %}

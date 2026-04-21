{#
    MariaDB 10.3+ supports INTERSECT as a set operator.
#}
{% macro mariadb__intersect() %}
    intersect
{% endmacro %}

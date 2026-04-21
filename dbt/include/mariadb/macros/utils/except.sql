{#
    MariaDB 10.3+ supports EXCEPT as a set operator.
#}
{% macro mariadb__except() %}
    except
{% endmacro %}

{% macro mariadb__cast_bool_to_text(field) %}
    case
        when ({{ field }}) is null then null
        when ({{ field }}) then 'true'
        else 'false'
    end
{% endmacro %}

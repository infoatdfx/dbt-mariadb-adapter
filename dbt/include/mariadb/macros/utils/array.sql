{#
    MariaDB has no native ARRAY type; JSON arrays are the closest equivalent.
    We emit JSON-backed implementations so cross-db models using dbt.array_*
    don't blow up on compile. Consumers should be aware that resulting
    "arrays" are really JSON documents.
#}

{% macro mariadb__array_construct(inputs, data_type) -%}
    {%- if inputs is none or inputs|length == 0 -%}
    cast('[]' as json)
    {%- else -%}
    json_array({{ inputs|join(', ') }})
    {%- endif -%}
{%- endmacro %}

{% macro mariadb__array_append(array, new_element) -%}
    json_array_append({{ array }}, '$', {{ new_element }})
{%- endmacro %}

{% macro mariadb__array_concat(array_1, array_2) -%}
    json_merge_preserve({{ array_1 }}, {{ array_2 }})
{%- endmacro %}

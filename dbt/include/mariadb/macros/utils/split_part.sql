{#
    MariaDB has no split_part, but SUBSTRING_INDEX returns everything up to
    (or after) the Nth delimiter. Chaining two of them isolates the Nth part.
    Negative `part_number` counts from the right (matching postgres behaviour).
#}
{% macro mariadb__split_part(string_text, delimiter_text, part_number) -%}
    {%- if part_number >= 0 -%}
    substring_index(
        substring_index({{ string_text }}, {{ delimiter_text }}, {{ part_number }}),
        {{ delimiter_text }},
        -1
    )
    {%- else -%}
    substring_index(
        substring_index({{ string_text }}, {{ delimiter_text }}, {{ part_number }}),
        {{ delimiter_text }},
        1
    )
    {%- endif -%}
{%- endmacro %}

{#
    MariaDB supports standard-SQL `POSITION(needle IN haystack)`. Default
    macro would work; we override to use the MariaDB-preferred LOCATE which
    returns 0 (not NULL) when not found.
#}
{% macro mariadb__position(substring_text, string_text) %}
    locate({{ substring_text }}, {{ string_text }})
{%- endmacro %}

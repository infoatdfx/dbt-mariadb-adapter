{#
    MariaDB ships a virtual `seq_M_to_N` table via the Sequence storage engine,
    which is enabled by default. Use it directly instead of emulating with
    power-of-two CTEs the way the global default does.

    Docs: https://mariadb.com/kb/en/sequence-storage-engine/
#}

{% macro mariadb__generate_series(upper_bound) %}
    select seq as generated_number
    from seq_1_to_{{ upper_bound }}
{% endmacro %}

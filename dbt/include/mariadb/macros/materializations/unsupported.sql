{#
  Explicit rejections for materializations that dbt-core knows about but
  MariaDB can't provide. Without these, users get a generic
  "materialization not found" error that's easy to misdiagnose.
#}

{% materialization materialized_view, adapter='mariadb' %}
    {%- do exceptions.raise_compiler_error(
        "MariaDB does not support materialized views. "
        "Use `materialized: view` for lightweight reuse, or "
        "`materialized: table` / `materialized: incremental` for materialised output."
    ) -%}
{% endmaterialization %}

{% materialization dynamic_table, adapter='mariadb' %}
    {%- do exceptions.raise_compiler_error(
        "MariaDB does not have a dynamic_table concept. "
        "Use `materialized: incremental` for near-real-time tables."
    ) -%}
{% endmaterialization %}

{#
  Incremental materialization for MariaDB.

  Dispatches to a strategy-specific helper that emits the `main` statement
  SQL. Strategies supported:
    - append
    - delete+insert   (default)
    - merge           (INSERT … ON DUPLICATE KEY UPDATE; requires a unique
                       PRIMARY/UNIQUE constraint on `unique_key`)
    - microbatch      (DELETE+INSERT filtered by event_time window)

  `MariaDBAdapter.valid_incremental_strategies()` keeps this list in sync
  with what dbt-core lets through; unknown strategies raise a clear error
  before compile.
#}

{% macro mariadb__get_incremental_default_sql(arg_dict) %}
    {{ return(mariadb__get_incremental_delete_insert_sql(arg_dict)) }}
{% endmacro %}

{% materialization incremental, adapter='mariadb' %}

  {%- set unique_key = config.get('unique_key') -%}
  {%- set strategy = config.get('incremental_strategy') or 'delete+insert' -%}
  {%- set valid = ['append', 'delete+insert', 'merge', 'microbatch'] -%}
  {%- if strategy not in valid -%}
    {%- do exceptions.raise_compiler_error(
        "Invalid incremental_strategy '" ~ strategy ~ "' for adapter 'mariadb'. "
        "Valid strategies: " ~ valid | join(', ')
    ) -%}
  {%- endif -%}

  {% set target_relation = this.incorporate(type='table') %}
  {% set existing_relation = load_relation(this) %}
  {% set tmp_relation = make_temp_relation(this) %}

  {{ run_hooks(pre_hooks, inside_transaction=False) }}
  {{ run_hooks(pre_hooks, inside_transaction=True) }}

  {% set to_drop = [] %}

  {% if existing_relation is none %}
      {#- First run: just CTAS -#}
      {% set build_sql = create_table_as(False, target_relation, sql) %}

  {% elif existing_relation.is_view or should_full_refresh() %}
      {#- Rebuild: rename the old one out of the way, recreate, drop later -#}
      {% set backup_identifier = existing_relation.identifier ~ "__dbt_backup" %}
      {% set backup_relation = existing_relation.incorporate(path={"identifier": backup_identifier}) %}
      {% do adapter.drop_relation(backup_relation) %}
      {% do adapter.rename_relation(target_relation, backup_relation) %}
      {% set build_sql = create_table_as(False, target_relation, sql) %}
      {% do to_drop.append(backup_relation) %}

  {% else %}
      {#- Incremental: land the new batch in a temp table, then dispatch -#}
      {% do run_query(create_table_as(True, tmp_relation, sql)) %}
      {% do adapter.expand_target_column_types(
             from_relation=tmp_relation,
             to_relation=target_relation) %}
      {% set dest_columns = adapter.get_columns_in_relation(target_relation) %}
      {% set arg_dict = {
            "target_relation": target_relation,
            "temp_relation": tmp_relation,
            "unique_key": unique_key,
            "dest_columns": dest_columns,
      } %}

      {% if strategy == 'append' %}
          {% set build_sql = mariadb__get_incremental_append_sql(arg_dict) %}
      {% elif strategy == 'merge' %}
          {% set build_sql = mariadb__get_incremental_merge_sql(arg_dict) %}
      {% elif strategy == 'microbatch' %}
          {% set build_sql = mariadb__get_incremental_microbatch_sql(arg_dict) %}
      {% else %}
          {% set build_sql = mariadb__get_incremental_delete_insert_sql(arg_dict) %}
      {% endif %}
  {% endif %}

  {% call statement("main") %}
      {{ build_sql }}
  {% endcall %}

  {% do persist_docs(target_relation, model) %}

  {{ run_hooks(post_hooks, inside_transaction=True) }}
  {% do adapter.commit() %}

  {% for rel in to_drop %}
      {% do adapter.drop_relation(rel) %}
  {% endfor %}

  {{ run_hooks(post_hooks, inside_transaction=False) }}

  {{ return({'relations': [target_relation]}) }}

{%- endmaterialization %}

{#
  Strategy helpers used by the incremental materialization. Each emits the
  SQL that goes into the `main` statement for a given incremental_strategy.
#}

{% macro mariadb__get_incremental_append_sql(arg_dict) -%}
    {%- set target = arg_dict["target_relation"] -%}
    {%- set source = arg_dict["temp_relation"] -%}
    {%- set dest_cols_csv = arg_dict["dest_columns"] | map(attribute='quoted') | join(', ') -%}

    insert into {{ target }} ({{ dest_cols_csv }})
    (
        select {{ dest_cols_csv }}
        from {{ source }}
    )
{%- endmacro %}

{% macro mariadb__get_incremental_delete_insert_sql(arg_dict) -%}
    {%- set target = arg_dict["target_relation"] -%}
    {%- set source = arg_dict["temp_relation"] -%}
    {%- set unique_key = arg_dict["unique_key"] -%}
    {%- set dest_cols_csv = arg_dict["dest_columns"] | map(attribute='quoted') | join(', ') -%}

    {% if unique_key is not none and unique_key|length %}
    {%- set unique_key_csv = unique_key if unique_key is string else unique_key | join(',') -%}
    delete from {{ target }}
    where ({{ unique_key_csv }}) in (
        select {{ unique_key_csv }}
        from {{ source }}
    );
    {% endif %}

    insert into {{ target }} ({{ dest_cols_csv }})
    (
        select {{ dest_cols_csv }}
        from {{ source }}
    )
{%- endmacro %}

{% macro mariadb__get_incremental_merge_sql(arg_dict) -%}
    {#
      MariaDB has no standard MERGE. Emulate via INSERT ... ON DUPLICATE KEY UPDATE.
      This REQUIRES that `unique_key` maps to an actual PRIMARY KEY or UNIQUE
      constraint on the target table; otherwise the ON DUPLICATE branch never
      fires and you'll get plain inserts (with duplicates).
    #}
    {%- set target = arg_dict["target_relation"] -%}
    {%- set source = arg_dict["temp_relation"] -%}
    {%- set unique_key = arg_dict["unique_key"] -%}
    {%- set dest_columns = arg_dict["dest_columns"] -%}
    {%- set dest_cols_csv = dest_columns | map(attribute='quoted') | join(', ') -%}

    {% if unique_key is none or unique_key|length == 0 %}
        {% do exceptions.raise_compiler_error(
            "incremental_strategy='merge' on MariaDB requires a unique_key "
            "matching a PRIMARY KEY or UNIQUE index on the target table."
        ) %}
    {% endif %}

    {%- set update_clauses = [] -%}
    {%- for col in dest_columns -%}
        {%- do update_clauses.append(col.quoted ~ ' = VALUES(' ~ col.quoted ~ ')') -%}
    {%- endfor -%}

    insert into {{ target }} ({{ dest_cols_csv }})
    (
        select {{ dest_cols_csv }}
        from {{ source }}
    )
    on duplicate key update
        {{ update_clauses | join(',\n        ') }}
{%- endmacro %}

{% macro mariadb__get_incremental_microbatch_sql(arg_dict) -%}
    {#
      Microbatch: delete rows in the current batch window from the target,
      then insert the batch (which was already filtered to the window by
      dbt-core via {{ this }} SQL). The window bounds come from the model
      config (`event_time`) and the batch fixture dbt sets at runtime.
    #}
    {%- set target = arg_dict["target_relation"] -%}
    {%- set source = arg_dict["temp_relation"] -%}
    {%- set dest_cols_csv = arg_dict["dest_columns"] | map(attribute='quoted') | join(', ') -%}
    {%- set event_time = model.config.event_time -%}

    {% if event_time is none or event_time|length == 0 %}
        {% do exceptions.raise_compiler_error(
            "incremental_strategy='microbatch' requires `event_time` to be set "
            "on the model config."
        ) %}
    {% endif %}

    delete from {{ target }}
    where {{ adapter.quote(event_time) }} >= '{{ model.config.__dbt_internal_microbatch_event_time_start }}'
      and {{ adapter.quote(event_time) }} <  '{{ model.config.__dbt_internal_microbatch_event_time_end }}';

    insert into {{ target }} ({{ dest_cols_csv }})
    (
        select {{ dest_cols_csv }}
        from {{ source }}
    )
{%- endmacro %}


{#  Legacy helpers kept so pre-existing dispatch callers keep working. Newer
    dispatch goes through mariadb__get_incremental_<strategy>_sql above. #}

{% macro incremental_delete(tmp_relation, target_relation, unique_key=none, statement_name="pre_main") %}
    {%- if unique_key is not none and unique_key|length -%}
    delete
    from {{ target_relation }}
    where ({{ unique_key if unique_key is string else unique_key | join(',') }}) in (
        select {{ unique_key if unique_key is string else unique_key | join(',') }}
        from {{ tmp_relation }}
    )
    {%- endif %}
{%- endmacro %}

{% macro incremental_insert(tmp_relation, target_relation, unique_key=none, statement_name="main") %}
    {%- set dest_columns = adapter.get_columns_in_relation(target_relation) -%}
    {%- set dest_cols_csv = dest_columns | map(attribute='quoted') | join(', ') -%}

    insert into {{ target_relation }} ({{ dest_cols_csv }})
    (
       select {{ dest_cols_csv }}
       from {{ tmp_relation }}
    )
{%- endmacro %}

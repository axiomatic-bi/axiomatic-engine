{% macro to_title_case(column_expression) -%}
    case
        when {{ column_expression }} is null then null
        else array_to_string(
            [
                upper(word[1:1]) || lower(word[2:])
                for word in string_split(trim(cast({{ column_expression }} as varchar)), ' ')
            ],
            ' '
        )
    end
{%- endmacro %}

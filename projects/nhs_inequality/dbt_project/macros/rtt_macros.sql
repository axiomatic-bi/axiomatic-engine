{#
  NHS RTT Macros
  Reusable SQL generators for RTT waiting time band calculations
#}

{% macro sum_week_bands(start_week, end_week) %}
{#
  Generates a sum of coalesced week band columns from start_week to end_week.
  Used for calculating breach counts (18+, 52+, 65+, 78+, 104+ weeks).
#}
{% set bands = [] %}
{% for week in range(start_week, end_week + 1) %}
  {% if week < 52 %}
    {% set _ = bands.append("coalesce(cast(weeks_" ~ week ~ "_to_" ~ (week + 1) ~ " as integer), 0)") %}
  {% elif week == 104 %}
    {% set _ = bands.append("coalesce(cast(weeks_over_104 as integer), 0)") %}
  {% else %}
    {% set _ = bands.append("coalesce(cast(weeks_" ~ week ~ "_to_" ~ (week + 1) ~ " as integer), 0)") %}
  {% endif %}
{% endfor %}
{{ bands | join(' + ') }}
{% endmacro %}

{% macro count_over_18_weeks() %}
{# Sum all week bands from 18-19 through 104+ #}
{{ sum_week_bands(18, 104) }}
{% endmacro %}

{% macro count_over_52_weeks() %}
{# Sum all week bands from 52-53 through 104+ #}
{{ sum_week_bands(52, 104) }}
{% endmacro %}

{% macro count_over_65_weeks() %}
{# Sum all week bands from 65-66 through 104+ #}
{{ sum_week_bands(65, 104) }}
{% endmacro %}

{% macro count_over_78_weeks() %}
{# Sum all week bands from 78-79 through 104+ #}
{{ sum_week_bands(78, 104) }}
{% endmacro %}

{% macro count_over_104_weeks() %}
{# Just the 104+ week band #}
coalesce(cast(weeks_over_104 as integer), 0)
{% endmacro %}

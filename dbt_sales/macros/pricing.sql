
{% macro discounted_amount(extended_price, discount_percent, scale=2) %}
    ( -1 * {{extended_price}} * {{discount_percent}} )::decimal(16, {{ scale }})
{% endmacro %}

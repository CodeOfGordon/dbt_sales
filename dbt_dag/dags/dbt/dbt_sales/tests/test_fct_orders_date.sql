/* check if order dates are valid i.e. chronologically sound */
select
    order_key, order_date
from 
    {{ ref('fct_orders') }}
where
    date(order_date) > CURRENT_DATE()
    or date(order_date) < date('1970-01-01') /* arbitrary date -> just check if date was too long ago -> red flag if born long before db was made */

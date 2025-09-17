

1. Set up Snowflake and create necessary roles and permissions
Here I created an `analytics` role and assigned it to my user account. Afterwards, I set up the roles, datawarehouse, and database; which can be seen in [!dbt_sales_perm_setup.sql].

2. Set up dbt
[dbt_2a]
[dbt_2b]

Here, I installed `dbt-snowflake` and set up the connection to snowflake. I wanted to authenticate via key-pairs, so before this, I generated it according to Snowflake's requirements
Note: when using SSH key-pairs for authentication, Snowflake requires the key to be in PKCS#8 format, otherwise it may not recognize it when authenticating.

3. Set up directories
- https://docs.getdbt.com/best-practices/how-we-structure/2-staging
- https://www.getdbt.com/blog/modular-data-modeling-techniques


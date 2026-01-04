In this project, I create a data pipeline by sourcing data from Snowflake, using dbt to standardize schemas & actually build the pipeline, and orchestrating the DAG deployment in Airflow.

Throughout this data pipeline, we will be using the `tpch_sf1` table from the `snowflake_sample_data` database in Snowflake. This database generally provides many tables that are considered a decision support benchmark for broad industry-wide relevance, which provides a good dataset for us.


# 1. Set up Snowflake and create necessary roles and permissions
Here I created an `analytics` role and assigned it to my user account. Afterwards, I set up the roles, datawarehouse, and database; which can be seen in [here](dbt_sales_perm_setup.sql).

# 2. Set up dbt
After installing the dbt adapter for snowflake by `pip install dbt-snowflake`

![setting up ssh keypair on dbt side](/imgs/dbt_2a.png)
![setting up ssh keypair on snowflake side](/imgs/dbt_2b.png)
![dbt init](/imgs/dbt_2c.png)

Here, I installed `dbt-snowflake` and set up the connection to snowflake. I wanted to authenticate via key-pairs, so before this, I generated it according to Snowflake's requirements

*Note: when using SSH key-pairs for authentication, Snowflake requires the key to be in PKCS#8 format, otherwise it may not recognize it when authenticating.*

Afterwards, I placed the public key into snowflake and connected it (this is done at a user level), so now any dbt project I do will have access to my snowflake account. This can be double checked by running `dbt debug` when trying to access any of the items in snowflake, and it confirms the connection.

Now that I've set up the snowflake keypair with dbt, I can safely initialize my dbt project as shown above.
- Note: you can find the account identifier by clicking the `user account button` (bottom left) > Account (cloud platform icon e.g. AWS) > `View Account details`. Here, you'll see a bunch of details including the account identifier.
    - If something goes wrong, you can always edit the dbt config file at `~/.dbt/profile.yml`

# 3. Installed extra db package

- Installed db_utils in [packages.yml](/dbt_dag/dags/dbt/dbt_sales/packages.yml)


# 4. Set up directories
- https://docs.getdbt.com/best-practices/how-we-structure/2-staging
- https://www.getdbt.com/blog/modular-data-modeling-techniques


__Best Practice__
When setting up folder structure
- in staging, split up by data source
- in marts, split up by what makes sense in your business context (e.g. by department)

When staging
- don't join nor aggregate, we just want the clean data as raw as possible, similar to raw fact tables in PowerBI


As a result, we create the folders,
- `staging` -- where we store raw data
- `marts` -- where we do the actual transformation
under the `models` folder.

In dbt, we have the following pipeline and their naming conventions:
raw data (no prefix)
   ↓
staging models (prefix: `stg_`)
   ↓
intermediate models (prefix: `int_`)
   ↓
marts (prefix: `fct_` / `dim_`)

<br>

- raw data -- these exist in your data warehouse (i.e. Snowflake in our case), they're the bare bones tables
- intermediate models -- transformed and/or combined staging models, used for the final table (i.e. the marts)

# 5. Staging

We would like to grab the orders and orders related data, and to do so, we define the source definition file [`tpch_sources.yml`](/dbt_dag/dags/dbt/dbt_sales/models/staging/snowflake/tpch_sources.yml), which structures and tests if the table coming from the database fits our requirements; standardizing the schema.
- Note: the names of the table, columns, etc have to match what's shown in the database, since we're specifying **what source** we're pulling the data/metadata from

We can now use this source definition file to create a database view with Jinja syntax, which can be seen in [stg_tpch_orders.sql](/dbt_dag/dags/dbt/dbt_sales/models/staging/snowflake/stg_tpch_orders.sql), where we create a script for the orders column.

Now going back into snowflake, we can see the script created the view in the database we specified when we initialized the project. This is one of the key strengths of dbt, as it allows databases to effectively see each other in a standardized way.
[step 4a](/imgs/dbt_5.png)

We also create a sql script for the lineitems columns seen in [`stg_tpch_lineitems.sql`](/dbt_dag/dags/dbt/dbt_sales/models/staging/snowflake/stg_tpch_lineitems.sql)
- Note: we also create a surrogate key (i.e. SK) to uniquely select a row in `lineitem` since `orders` has a one-to-many relationship with `lineitem`, meaning we can't granularly select a row without doing this.
We can specifically run this sql script by running `dbt run -s stg_tpch_lineitems`


# 6. Model (Mart)

In data modelling design, there are 2 main tables
- fact table -- the main table(s) and has quantitative data
- dimension table -- the additional table(s) that provide descriptive context to said fact table(s), i.e. mostly houses qualitative data

In a **star schema**, there's typically a fact table in the middle with dimension tables connected to it via their foreign key
[star schema](/imgs/star_schema.png)
When creating the files for these tables, the naming convention in dbt is to have fact tables prefix `fct_`, and dimension tables prefix `dim_`.


With that said, we now join the tables by combining them based on the FK (`order_key`), which can be seen [here](/dbt_dag/dags/dbt/dbt_sales/models/intermediate/int_order_items.sql).
- Note that both of these tables (`lineitems` and `orders`) are fact tables

Notice in the script, there is an unfamiliar `items_discount_amount` field, acting almost like a function. This was created via __macros__.

# 7. Macros

In dbt, we like to keep things D.R.Y.
- D: Don't
- R: Repeat
- Y: Yourself
i.e. keep things modular, and create functions if you begin to repeat actions

Typically, we use it to define metrics/formulas we would like to use, seen [here](/dbt_dag/dags/dbt/dbt_sales/macros/pricing.sql)

Notice that if you were to look at the script where this this macro is used (i.e. the intermediate tables [here](/dbt_dag/dags/dbt/dbt_sales/models/intermediate/int_order_items.sql) or [here](/dbt_dag/dags/dbt/dbt_sales/models/intermediate/int_order_items_summary.sql)), you may notice that the function `discounted_amount` has its parameters wrapped in string quotes. This has to do with Jinja, which is a template engine that dbt uses during the compiling phase to handle replacing the macro calls (i.e. the functions you see in the above script) with the macro script, before converting them into SQL equivalent code under the hood. This code is stored as raw string, and once Jinja finishes the replacing the templates, dbt converts the raw string into an SQL query and executes it.
If we didn't wrap the parameters in string quotes, Jinja wouldn't be able to grab the sql objects/alias, since it goes through files before the SQL query is executed; so all it sees are undefined variables. However, if these objects are instead strings, then Jinja can take these values, and add them into dbt's internal SQL raw string in order to later be executed.


# 8. Model (Mart) Cont.

Along with the intermediate tables [int_order_items.sql](/dbt_dag/dags/dbt/dbt_sales/models/intermediate/int_order_items.sql) and [int_order_items_summary.sql](/dbt_dag/dags/dbt/dbt_sales/models/intermediate/int_order_items_summary.sql), we create a fact table which joins an intermediate and staging table. This can be seen [here](/dbt_dag/dags/dbt/dbt_sales/models/marts/fct_orders.sql)


# 9. Testing (Model Schema Testing)

Now that we have the schemas set, we would like to create tests in order to continuously valaidate if the tables coming from our sources (the datawarehouses i.e. Snowflake) are following our rules.

In truth, we already did this when we first sourced our data with [tpch_sources](/dbt_dag/dags/dbt/dbt_sales/models/staging/snowflake/tpch_sources.yml).

We do so [again](/dbt_dag/dags/dbt/dbt_sales/models/marts/_marts_test.yml) but at the mart (modelling) stage to validate again, which would be vital if we had multiple data sources (typical in a bigger project).


# 10. Singular Tests

Now that we've tested the source and models in general, we create additional unit tests to granularly check certain columns to see if they're valid.

This can be seen in [here](/dbt_dag/dags/dbt/dbt_sales/tests/test_fct_orders_discount.sql) and [here](/dbt_dag/dags/dbt/dbt_sales/tests/test_fct_orders_date.sql).

# 11. Orchestrating with Airflow via Astronomer Cosmos

In order to simplify the process, we will use the Astronomer Cosmos open source project, which manages Airflow behind the scenes when using it with dbt.

To do this, we first install astro into your system. 

`curl -sSL install.astronomer.io | sudo bash -s`

Afterwards, I created a script to hook up the dbt code with the DAG used by Astronomer [here](/dbt_dag/dags/dbt_dag.py).

Finally, I ran `astro dev init` to spin up the managed Airflow containers, and entered the Snowflake necessary credentials.

The result is that I now have managed Airflow containers that orchestrate tasks to gather data from various sources (in our case, Snowflake's sample data) to be placed into the Snowflake database, where dbt plays the role of ensuring data integrity and validation. 

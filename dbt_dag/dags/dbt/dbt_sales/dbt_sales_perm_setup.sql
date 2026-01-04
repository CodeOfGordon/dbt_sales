use role accountadmin;

-- setup
create warehouse if not exists dbt_wh with warehouse_size='x-small';
create database if not exists dbt_db;
create role if not exists dbt_role;
create schema if not exists dbt_db.dbt_schema;
-- setup perms
show grants on warehouse dbt_wh;
grant usage on warehouse dbt_wh to role dbt_role;
grant usage on database dbt_db to role dbt_role;
grant role dbt_role to role analytics;
grant create view, create table on schema dbt_db.dbt_schema to role dbt_role;
grant select, insert, update on all tables in schema dbt_db.dbt_schema to role dbt_role;
grant select, insert, update on future tables in schema dbt_db.dbt_schema to role dbt_role;


-- use role
use role dbt_role

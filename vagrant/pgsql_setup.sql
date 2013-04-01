create user vagrant with createdb password '';
create database vagrant with owner vagrant;
grant all on database vagrant to vagrant;
\c template1
create extension tablefunc;

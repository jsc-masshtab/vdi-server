create table pool_role_m2m (
    pool integer not null,
    role varchar(20),
    constraint pool_role_pk primary key (pool, role)
);
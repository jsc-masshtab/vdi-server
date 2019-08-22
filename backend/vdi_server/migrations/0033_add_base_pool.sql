create table base_pool (
    id serial,
    name varchar(100),
    controller_ip varchar(100),
    constraint controller_fk
        FOREIGN KEY (controller_ip) REFERENCES controller(ip),
    constraint base_pool_pk
        primary key (id)
);

alter table pool inherit base_pool;
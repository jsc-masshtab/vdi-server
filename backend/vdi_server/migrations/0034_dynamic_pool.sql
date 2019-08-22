create table static_pool (
    constraint controller_fk
        FOREIGN KEY (controller_ip) REFERENCES controller(ip),
    constraint static_pool_pk
        primary key (id)
) inherits (base_pool);
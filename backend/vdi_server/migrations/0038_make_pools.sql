create table dynamic_traits (
    id serial,
    initial_size integer,
    reserve_size integer,
    total_size integer,
    datapool_id varchar(100),
    cluster_id varchar(100),
    node_id varchar(100),
    vm_name_template varchar(100),

    constraint dynamic_traits_pk primary key (id)
);

alter table pool
    add column dynamic_traits integer;

alter table pool
    add constraint pool_dynamic_traits_fk FOREIGN KEY (dynamic_traits) REFERENCES dynamic_traits(id);
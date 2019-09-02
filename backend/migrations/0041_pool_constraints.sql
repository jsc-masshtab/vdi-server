alter table pools_users
    drop constraint pool_fk;
alter table pools_users
    add constraint pool_fk
    foreign key (pool_id) references pool (id);
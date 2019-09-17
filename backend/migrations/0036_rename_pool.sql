alter table pool rename to dynamic_pool;
alter table base_pool rename to pool;

alter table vm
    drop constraint vm_pool_fk;
alter table vm
    add constraint "vm_pool_fk" FOREIGN KEY (pool_id) REFERENCES pool(id);


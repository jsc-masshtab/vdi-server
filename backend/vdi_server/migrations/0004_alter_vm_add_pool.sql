alter table vm add column pool_id int not null;

alter table vm add constraint vm_pool_fk
	foreign key (pool_id) references pool (id);
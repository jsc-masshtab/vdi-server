alter table pool
    drop constraint pool_dynamic_traits_fk,
    add column template_id varchar(100),
	add column initial_size int,
	add column reserve_size int,
	add column total_size int,
	add column vm_name_template varchar(100);

drop table dynamic_traits;

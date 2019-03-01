create table pool
(
    id serial,
	template_id varchar(100),
	name varchar(100),
	initial_size int,
	reserve_size int,

	constraint pool_pk
		primary key (id),
    constraint pool_templatevm_fk
		foreign key (template_id) references vm (id)

);
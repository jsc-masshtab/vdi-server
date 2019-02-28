create table vm
(
	id varchar(100),
	is_template boolean DEFAULT 'no',
	constraint vm_pk
		primary key (id)
);

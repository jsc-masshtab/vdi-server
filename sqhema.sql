create table pool
(
	template_id varchar(100),
	constraint pool_pk
		primary key (template_id),
  constraint pool_templatevm_fk
		foreign key (template_id) references templatevm (id)

);

create table templatevm
(
	id varchar(100),
	constraint templatevm_pk
		primary key (id)
);

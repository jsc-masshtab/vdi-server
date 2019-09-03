create table veil_vm
(
	id varchar(100),
	constraint veil_vm_pk
		primary key (id)
);

CREATE TABLE vm (
  state      varchar(20),

  constraint vm_pk
		primary key (id)

) inherits (veil_vm);
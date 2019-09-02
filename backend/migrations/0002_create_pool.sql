create table pool
(
  id serial,
	template_id varchar(100),
	name varchar(100),
	initial_size int,
	reserve_size int,

	constraint pool_pk primary key (id)

);


create table default_controller
(
    ip varchar(100),

    UNIQUE(ip),

	constraint default_controller_pk
		primary key (ip),
    constraint default_controller_fk
		foreign key (ip) references controller (ip)

);


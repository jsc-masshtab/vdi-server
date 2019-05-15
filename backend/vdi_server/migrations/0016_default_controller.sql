

create table default_controller
(
    ip varchar(100),
    unique_label varchar(6) CHECK (unique_label = 'unique'),

    UNIQUE(unique_label),

	constraint default_controller_pk
		primary key (ip),
    constraint default_controller_fk
		foreign key (ip) references controller (ip)

);
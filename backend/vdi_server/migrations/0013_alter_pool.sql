alter table pool
    add column controller_ip varchar(100),
    add column datapool_id varchar(100) not null,
    add column cluster_id varchar(100) not null,

    add constraint controller_fk
	    foreign key (controller_ip) references controller (ip);
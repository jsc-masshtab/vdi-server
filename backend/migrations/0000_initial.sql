
CREATE TYPE desktop_pool_type AS ENUM ('AUTOMATED', 'STATIC');

create table veil_vm
(
	id varchar(100),
	template_id varchar(100),
	constraint veil_vm_pk
		primary key (id)
);

create table vm (
    pool_id int not null,
    username varchar(100),
    constraint vm_pk
        primary key (id),
    constraint vm_pool_fk
        foreign key (pool_id) references pool (id)
) inherits (veil_vm);

create table pool (
    id serial,
    name varchar(100),
    controller_ip varchar(100),
    desktop_pool_type desktop_pool_type,
    dynamic_traits integer,
    datapool_id varchar(100),
    cluster_id varchar(100),
    node_id varchar(100),
    template_id varchar(100),
	initial_size int,
	reserve_size int,
	total_size int,
	vm_name_template varchar(100),
    deleted boolean,
    constraint base_pool_pk
        primary key (id)
    constraint controller_fk
        FOREIGN KEY (controller_ip) REFERENCES controller(ip),
);

create table "user"
(
    username varchar(100),
    password varchar(128) not null,
    email varchar(254),
    user_group varchar(20),
    date_joined timestamp with time zone default now(),
    constraint user_pk
        primary key (username),
    constraint user_group_fk
        foreign key (user_group) references user_group (alias)
);

create table pools_users
(
    pool_id int,
    username varchar(100),
    constraint pools_users_pk
        primary key (pool_id, username),
    constraint pool_fk
        foreign key (pool_id) references pool (id),
    constraint user_fk
        foreign key (username) references public.user (username)
);

create table controller
(
	ip varchar(100),
	description varchar(100),
	constraint controller_pk
		primary key (ip)
);

create table default_controller
(
    ip varchar(100),
    UNIQUE(ip),
	constraint default_controller_pk
		primary key (ip),
    constraint default_controller_fk
		foreign key (ip) references controller (ip)
);

create table permission (
    alias varchar(20) not null,
    description varchar(100),
    constraint permission_pk primary key (alias)
);

create table role (
    alias varchar(20) not null,
    description varchar(100),
    date_created timestamp with time zone default now(),
    constraint user_group_pk primary key (alias)
);

create table user_role_m2m (
    username varchar(100),
    role varchar(20)
);

create table veil_creds (
    username varchar(100),
    token varchar(1024),
    controller_ip varchar(100) not null,
    expires_on timestamp with time zone not null,
    constraint veil_creds_pk
        primary key (username, controller_ip)
);

create table pool_role_m2m (
    pool_id integer not null,
    role varchar(20),
    constraint pool_role_pk primary key (pool, role)
);

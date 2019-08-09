create table permission (
    alias varchar(20) not null,
    description varchar(100),
    constraint permission_pk primary key (alias)
);

create table user_group (
    alias varchar(20) not null,
    description varchar(100),
    constraint user_group_pk primary key (alias)
);

alter table public.user
    add column user_group varchar(20);

alter table public.user
    add constraint user_group_fk foreign key (user_group) references user_group (alias);


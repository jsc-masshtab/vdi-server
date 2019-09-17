alter table public.user
    drop column user_group;

alter table user_group rename to role;

create table user_role_m2m (
  username varchar(100),
  role varchar(20)
);
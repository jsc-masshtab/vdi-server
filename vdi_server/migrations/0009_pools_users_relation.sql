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
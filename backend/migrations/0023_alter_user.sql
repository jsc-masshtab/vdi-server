alter table public.user
    alter column password type varchar(128);

alter table public.user
    alter column password set not null;

alter table public.user
    alter column email type varchar(254);

alter table public.user
    alter column email set not null;

alter table public.user
    add column date_joined timestamp with time zone default now();
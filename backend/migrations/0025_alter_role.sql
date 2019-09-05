alter table role
    add column date_created timestamp with time zone default now();
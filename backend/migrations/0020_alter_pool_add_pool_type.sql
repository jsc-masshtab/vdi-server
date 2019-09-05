CREATE TYPE desktop_pool_type AS ENUM ('AUTOMATED', 'STATIC');
alter table pool
    add desktop_pool_type desktop_pool_type;

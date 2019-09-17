alter table veil_creds drop constraint veil_creds_pk;

alter table veil_creds add constraint veil_creds_pk
  primary key (username, controller_ip);
# http://coussej.github.io/2015/09/15/Listening-to-generic-JSON-notifications-from-PostgreSQL-in-Go/

INIT = """
CREATE TABLE users
(
  name character varying(63) unique,
  connected boolean default TRUE,
  ts timestamp not null default CURRENT_TIMESTAMP
);

CREATE TABLE messages
(
  id serial primary key,
  username character varying(63) references users(name) not null,
  message text,
  ts timestamp not null default CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION notify_messages() RETURNS TRIGGER AS $$
    DECLARE 
        data json;
    BEGIN
        PERFORM pg_notify('events', row_to_json(NEW)::text);
        RETURN NULL; 
    END;
    
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_notify_messages AFTER INSERT ON messages
    FOR EACH ROW EXECUTE PROCEDURE notify_messages();

CREATE OR REPLACE FUNCTION notify_users() RETURNS TRIGGER AS $$
    DECLARE 
        data json;
        
    BEGIN
    
        SELECT json_agg(users.name) INTO STRICT data FROM users WHERE users.connected = TRUE;
        data = json_build_object('users', data);
        PERFORM pg_notify('events', data::text);
        RETURN NULL;
    END;
    
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_notify_users AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE PROCEDURE notify_users();
"""

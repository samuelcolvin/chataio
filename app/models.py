# http://coussej.github.io/2015/09/15/Listening-to-generic-JSON-notifications-from-PostgreSQL-in-Go/

INIT = """
CREATE TABLE messages
(
  id serial primary key,
  action character varying(63) not null,
  username character varying(63) not null,
  message text,
  ts timestamp not null default CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION notify_event() RETURNS TRIGGER AS $$
    BEGIN
        PERFORM pg_notify('events', row_to_json(NEW)::text);
        RETURN NULL; 
    END;
    
$$ LANGUAGE plpgsql;

CREATE TRIGGER notify_trigger AFTER INSERT ON messages
    FOR EACH ROW EXECUTE PROCEDURE notify_event();
"""

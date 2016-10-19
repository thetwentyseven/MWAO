DROP TABLE if EXISTS milkyway;

CREATE TABLE milkyway (
  id integer PRIMARY KEY autoincrement,
  type varchar(100) NOT NULL,
  name varchar(100) NOT NULL,
  description varchar(500) NOT NULL,
  size integer DEFAULT 0,
  mass integer DEFAULT 0,
  distance integer DEFAULT 0,
  discoverer varchar(100) NULL,
  image_url varchar(500) NULL
)

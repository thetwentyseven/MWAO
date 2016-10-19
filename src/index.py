import ConfigParser
import logging
import sqlite3

from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, url_for, g

app = Flask(__name__)

# Database
db_location = 'database/sqlite3.db'

def get_db():
  db = getattr(g, 'db', None)
  if db is None:
    db = sqlite3.connect(db_location)
    g.db = db
    return db

@app.teardown_appcontext
def close_db_connection(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

def init_db():
  with app.app_context():
    db = get_db()
    with app.open_resource('database/schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()


# Routes
@app.route('/')
def root():
    this_route = url_for('.root')
    app.logger.info("Logging a test message from "+this_route)

    return render_template('base.html'), 200


@app.route('/objects')
def objects():
    db = get_db()
    db.cursor().execute('insert into milkyway values (NULL, "Planet", "Earth", "Our planet", 6.371, 1, 0, "Unknown", "uploads/earth.png" )')
    db.commit()

    page = []
    page.append('<html><ul>')
    sql = "SELECT * FROM milkyway ORDER BY type"
    for row in db.cursor().execute(sql):
        page.append('<li>')
        page.append(str(row))
        page.append('</li>')

    page.append('</ul></html>')

    return ''.join(page)


# Configuration
def init(app):
  config = ConfigParser.ConfigParser()
  try:
      config_location = "etc/default.cfg"
      config.read(config_location)

      app.config['DEBUG'] = config.get("config", "debug")
      app.config['ip_address'] = config.get("config", "ip_address")
      app.config['port'] = config.get("config", "port")
      app.config['url'] = config.get("config", "url")
      app.config['log_file'] = config.get("logging", "name")
      app.config['log_location'] = config.get("logging", "location")
      app.config['log_level'] = config.get("logging", "level")
  except:
      print "Could not read configs from: ", config_location

# Logs
def logs(app):
  log_pathname = app.config['log_location']+app.config['log_file']
  file_handler = RotatingFileHandler(log_pathname, maxBytes = 1024*1024*10, backupCount = 1024)
  file_handler.setLevel(app.config['log_level'])
  formatter = logging.Formatter(" %(levelname)s | %(asctime)s | %(module)s | %(funcName)s | %(message)s" )
  file_handler.setFormatter(formatter)
  app.logger.setLevel(app.config['log_level'])
  app.logger.addHandler(file_handler)


if __name__ == "__main__":
  init(app)
  logs(app)
  app.run(
          host = app.config['ip_address'],
          port = int(app.config['port'])
          )

import ConfigParser
import logging
import sqlite3
import pprint
import os

from logging.handlers import RotatingFileHandler
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super secret key"

# Database
db_location = 'database/sqlite3.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

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


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

# Functions
def get_object(id):
    query = 'SELECT * FROM milkyway WHERE id = ?'
    object_id = query_db(query, [id], one=True)
    return object_id

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))

# Routes
@app.route('/')
def root():
    return render_template('home.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')

@app.errorhandler(401)
def unauthorized(error):
    return render_template('401.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['username']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['password']:
            error = 'Invalid password'
        else:
            session['logged'] = True
            return redirect(url_for('root'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged', None)
    flash('You were logged out')
    return redirect(url_for('root'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/objects/insert')
def insert():
    if not session.get('logged'):
        abort(401)
    return render_template('insert.html')

@app.route('/edit')
def edit():
    if not session.get('logged'):
        abort(401)
    return render_template('edit.html')

@app.route('/insert_value',methods = ['POST', 'GET'])
def insert_value():
    if not session.get('logged'):
        abort(401)
    g.db = sqlite3.connect(db_location)
    # Get all the content from the form
    atype = request.form['type']
    name = request.form['name']
    description = request.form['description']
    size = request.form['size']
    mass = request.form['mass']
    distance = request.form['distance']
    discoverer = request.form['discoverer']
    image_url = request.form['image_url']

    g.db.execute('INSERT INTO milkyway (type,name,description,size,mass,distance,discoverer,image_url) VALUES (?,?,?,?,?,?,?,?)',
    [atype, name, description, size, mass, distance, discoverer, image_url] )

    g.db.commit()
    return redirect(url_for('objects'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if not session.get('logged'):
        abort(401)
    g.db = sqlite3.connect(db_location)
    query = 'UPDATE milkyway SET type = ?, name = ?, description = ?, size = ?, mass = ?, distance = ?, discoverer = ?, image_url = ? WHERE id = ?'
    cur = g.db.cursor()
    cur.execute(query, [ request.form['type'], request.form['name'],request.form['description'], request.form['size'], request.form['mass'],request.form['distance'],request.form['discoverer'], request.form['image_url'], id])
    g.db.commit()
    return redirect(url_for('object', id=id))

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    if not session.get('logged'):
        abort(401)
    g.db = sqlite3.connect(db_location)
    cur = g.db.cursor()
    cur.execute('DELETE FROM milkyway WHERE id = ?', [id])
    g.db.commit()
    return redirect(url_for('objects'))

@app.route('/objects')
def objects():
    db = sqlite3.connect(db_location)
    query = db.execute('SELECT * FROM milkyway ORDER BY type')
    objects = [dict(id=row[0], type=row[1], name=row[2], description=row[3], size=row[4], mass=row[5],distance=row[6], discoverer=row[7], image_url=row[8]) for row in query.fetchall()]
    db.close()
    return render_template("objects.html",objects=objects)

@app.route('/objects/<category>')
def category(category):
    if category == None:
        abort(404)
    db = sqlite3.connect(db_location)
    query = db.execute('SELECT * FROM milkyway WHERE type = ? ORDER BY name', [category])
    objects = [dict(id=row[0], type=row[1], name=row[2], description=row[3], size=row[4], mass=row[5],distance=row[6], discoverer=row[7], image_url=row[8]) for row in query.fetchall()]
    db.close()
    return render_template("objects.html",objects=objects)

@app.route('/objects/view')
@app.route('/objects/view/<int:id>', methods=['GET', 'POST'])
def object(id):
    if session.get('logged'):
        object_id = get_object(id)
        if object_id:
            return render_template('edit.html', object_id=object_id)
    else:
        object_id = get_object(id)
        if object_id:
            return render_template('object.html', object_id=object_id)




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
      app.config['username'] = config.get("user", "username")
      app.config['password'] = config.get("user", "password")
      app.config['secret_key'] = config.get("user", "secret_key")
      app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

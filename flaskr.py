# -*- coding: utf-8 -*-
"""
    Flaskr
    ~~~~~~

    A microblog example application written as Flask tutorial with
    Flask and sqlite3.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        sqlite_db = sqlite3.connect(app.config['DATABASE'])
        sqlite_db.row_factory = sqlite3.Row
        top.sqlite_db = sqlite_db

    return top.sqlite_db


@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
      abort(401)
    title = request.form['title']
    content = request.form['text']
    if title == "" or content == "":
      error = "empty is not allowed"
      return redirect(url_for('show_entries'))
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/register', methods=['GET', 'POST'])
def register():
  error = None
  if request.method == 'POST':
    uname = request.form['username']
    password = request.form['password']
    confirm = request.form['password_confirm']
    print password, confirm, uname
    if password != confirm:
      error = 'password is not same'
    else:
      db = get_db()
      cur = db.execute('select uname, password from users order by id desc')
      users = cur.fetchall()
      if len(users) != 0:
        error = 'User name have been used'
        return render_template('register.html', error = error)
      else:
        flash('Register succ')
        db.execute('insert into users (uname, password) values (?, ?)',
                   [uname, password])
        db.commit()
        session['logged_in'] = True
        return redirect(url_for('show_entries'))
  return render_template('register.html',  error = error)

           
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
      name = request.form['username']
      db = get_db()
      cur = db.execute("select uname, password from users where uname=\'%s\' order by id desc"%(name))
      users = cur.fetchall()
      print users
      if len(users) == 0:
        error = 'User name does not exsits'
      elif request.form['password'] != users[0][1]:
        error = 'Invalid password'
      else:
        session['logged_in'] = True
        flash('You were logged in')
        return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

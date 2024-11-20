from flask import Flask, flash, render_template, request, url_for, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret key'

global username, password, email, classname, classcode


# db connecton function
def conn_db():
    conn = sqlite3.connect('database.db')
    return conn


conn = conn_db()
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,
email TEXT UNIQUE,password TEXT,classname TEXT,classcode TEXT)
            ''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,
message TEXT,timestamp TIME DEFAULT CURRENT_TIMESTAMP,
classname TEXT,
FOREIGN KEY (username) REFERENCES users(username))
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS class(
id INTEGER PRIMARY KEY AUTOINCREMENT,
classcode TEXT UNIQUE,
classname TEXT,
classadmin TEXT
)
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS pdf_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        pdf BLOB NOT NULL
    )
''')
conn.commit()
conn.close()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/start')
def start():
    return redirect(url_for('index'))


# return home page
@app.route('/index')
def index():
    return render_template('index.html')


# handle login information
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = conn_db()
        cursor = conn.cursor()
        cursor.execute(
            '''
        SELECT username,classname,classcode FROM users WHERE email=? AND password=?
        ''', (email, password))
        result = cursor.fetchone()
        if result:
            global classname, classcode
            username = result[0]
            classname = result[1]
            classcode = result[2]
            session['email'] = email
            session['username'] = username
            conn.commit()
            conn.close()
            return redirect(url_for('profile',email=email,
                                      username=username))

        else:
            flash('invalid email or password', 'error')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


#admin login page
@app.route('/adminl')
def adminl():
    return render_template('adminl.html')


#handle admin info
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == "admin@gmail.com" and password == "admin":
            return redirect(url_for('index'))
        else:
            return ('<h1>please this page is available for admin only</h1>')
    return redirect(url_for('adminl'))


# open signup form
@app.route('/signupform')
def signupform():
    return render_template('signupform.html')


# handle signup information
@app.route('/submit-signup', methods=['GET', 'POST'])
def submitsignup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        activationcode = request.form['activationcode']
        password = request.form['password']
        confirmpassword = request.form['confirmpassword']
        conn = conn_db()
        cursor = conn.cursor()
        if (email and username and activationcode and password
                and confirmpassword and password == confirmpassword):
            if password == confirmpassword:
                try:
                    classname = cursor.execute(
                        '''
                    SELECT classname FROM class
                    WHERE classcode=?
                    ''', (activationcode, )).fetchone()
                    classname = classname[0]
                    if classname:
                        cursor.execute(
                            '''
                               INSERT INTO users(
                               email,username,password,classname,classcode) VALUES(?,?,?,?,?)
                               ''', (email, username, password, classname,
                                     activationcode))
                        return redirect(
                            url_for('index', error='acount created, login'))
                except sqlite3.IntegrityError:
                    return render_template('signupform.html',
                                           error="email already exists")
                except Exception as e:
                    return render_template('signupform.html', error=str(e))

                finally:
                    conn.commit()
                    conn.close()
            else:
                return render_template('signupform.html',
                                       error='passwords do not match')

    return redirect(url_for('signupform'))


# create class
@app.route('/createclass')
def createclass():
    return render_template('createclass.html')


# createclass form
@app.route('/submit-createclass', methods=['POST', 'GET'])
def submitcreateclass():
    conn = conn_db()
    cursor = conn.cursor()
    classadmin = request.form['classadmin']
    classname = request.form['classname']
    classcode = request.form['classcode']

    if request.method == 'POST':
        if classadmin and classname and classcode:
            try:
                cursor.execute(
                    '''
                    INSERT INTO class( classcode,classname,classadmin) VALUES(?, ?, ?)
                    ''', (classcode, classname, classadmin))
                conn.commit()
                return redirect(url_for('index', error='classcreated'))
            except sqlite3.IntegrityError:
                return render_template('createclass.html',
                                       error='Class already exists.')
            except Exception as e:
                # Handle any other exceptions
                return render_template('createclass.html', error=str(e))
            finally:
                cursor.close()
                conn.close()
        else:
            return render_template('createclass.html',
                                   error='All fields are required.')
    else:
        cursor.close()
        conn.close()
        return redirect(url_for('createclass'))


# profile
@app.route('/profile', methods=['GET'])
def profile():
    if 'email' and 'username' in session:
        email = session['email']
        username = session['username']
        return render_template('profile.html',
                               email=email,
                               username=username,
                               classname=classname,
                               classcode=classcode)
    else:
        return redirect(url_for('index'))


#logout
@app.route('/logout')
def logout():
    if 'username' and 'email' in session:
        session.pop('email', None)
        session.pop('username', None)
        return redirect(url_for('index'))
    else:
        return redirect(url_for('profile'))


# leftiframe return
@app.route('/leftiframe')
def leftiframe():
    return render_template('leftiframe.html')


#academic
@app.route('/academic')
def academic():
    return render_template('academic.html')


# link in leftiframe
@app.route('/chat')
def chat():
    conn = conn_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    messages = cursor.execute(
        '''
    SELECT username,message, timestamp FROM messages
    WHERE classname=? ORDER BY TIMESTAMP ASC
    ''', (classname, )).fetchall()
    conn.commit()
    conn.close()
    return render_template('chat.html', messages=messages)


# handle chat messages
@app.route('/send-message', methods=['POST'])
def sendmessage():
    conn = conn_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    messages = cursor.execute(
        '''
    SELECT username,message, timestamp FROM messages
    WHERE classname=? ORDER BY TIMESTAMP ASC
    ''', (classname, )).fetchall()
    if request.method == 'POST':
        message = request.form['message']
        cursor.execute(
            '''
        INSERT INTO messages (username,message,classname) VALUES(?,?,?)
        ''', (session['username'], message, classname))
        conn.commit()
        conn.close()
        return redirect(url_for('chat'))
    else:
        return redirect(url_for('profile'))


# rightiframe return
@app.route('/rightiframe')
def rightiframe():
    conn = conn_db()
    conn.row_factory = sqlite3.Row  # get data by row names
    cursor = conn.cursor()
    users = cursor.execute(
        '''
    SELECT username,email FROM users WHERE classname=?
    ''', (classname, )).fetchall()
    conn.commit()
    conn.close()
    return render_template('rightiframe.html',
                           users=users,
                           classname=classname)


# centeriframe for displayed
@app.route('/centeriframe')
def centeriframe():
    return render_template('centeriframe.html')


# chating form
@app.route('/send', methods=['POST'])
def send():
    if request.method == 'POST':
        message = request.form['message']
        if message:
            return redirect(url_for('profile'))
        else:
            return "message can't be empty!"
    else:
        return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run(debug=True)

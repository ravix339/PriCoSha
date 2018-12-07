#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
from datetime import datetime, timedelta
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='PriCoSha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)

#Define a route to hello function
@app.route('/')
def index():
    if 'email' in session and session['email'][:6] != 'guest_':
        return redirect(url_for('home'))
    else:
        session['email'] = 'guest_' + str(abs(hash(datetime.now())))
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/home')
def home():
    email = session['email']
    if email[:6]=='guest_':
        isGuest = 'yes'
    else:
        isGuest='no'
    cursor = conn.cursor()
    query = 'SELECT post_time, item_id, email_post, file_path, item_name FROM ContentItem as S WHERE ((is_pub = 0 AND %s IN ( SELECT DISTINCT email FROM belong WHERE belong.fg_name IN ( SELECT fg_name FROM belong WHERE belong.email=s.email_post))) OR is_pub=1) AND post_time >= DATE_SUB(NOW(), INTERVAL 1 DAY) ORDER BY post_time DESC'
    cursor.execute(query, (email))
    data = cursor.fetchall()
    print(data)
    cursor.close()
    return render_template('home.html', email=email, posts=data, isGuest=isGuest)

@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    email = request.form['email']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s and password = SHA2(%s, 256)'
    cursor.execute(query, (email, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['email'] = email
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or email'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    email = request.form['username']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s'
    cursor.execute(query, (email))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, SHA2(%s, 256), %s, %s)'
        cursor.execute(ins, (email, password, fname, lname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/post', methods=['GET', 'POST'])
def post():
    email = session['email']
    cursor = conn.cursor()
    item_name = request.form['title']
    filepath = request.form['filepath']
    is_pub = request.form['is_pub']
    query = 'INSERT INTO contentitem (email_post, post_time, file_path, item_name, is_pub) VALUES(%s, CURRENT_TIMESTAMP, %s, %s, %s)'
    cursor.execute(query, (email, filepath, item_name, is_pub))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/viewContent', methods=['POST'])
def viewContent():
    email_add = session['email']
    item_id = request.form['id']
    session['item_id'] = item_id
    cursor = conn.cursor()
    query = 'SELECT * FROM contentitem WHERE item_id=%s'
    cursor.execute(query, (item_id))
    content_info = cursor.fetchone()

    query = 'SELECT person.email, person.fname, person.lname FROM person WHERE person.email IN (SELECT email_tagged FROM tag WHERE tag.item_id=%s AND tag.status=%s)'
    cursor.execute(query, (item_id, 'yes'))
    tag_info = cursor.fetchall()

    query = 'SELECT email, rate_time, emoji FROM rate WHERE item_id=%s'
    cursor.execute(query, (item_id))
    rating_info = cursor.fetchall()

    query = 'SELECT email, commenttime, comment FROM comment WHERE item_id=%s'
    cursor.execute(query, (item_id))
    comment_info = cursor.fetchall()

    cursor.close()

    return render_template('viewContent.html', email=email_add, content=content_info, tag=tag_info, rating=rating_info, comments=comment_info)

@app.route('/rate_comment', methods=['GET', 'POST'])
def rate_comment():
    email = session['email']
    item_id = request.form['id']
    try:
        comment = request.form['comment']
        rate = request.form['rating']
        cursor = conn.cursor()
        if comment != '':
            query = 'INSERT INTO comment (email, comment, item_id) VALUES (%s, %s, %s)'
            cursor.execute(query, (email, comment, item_id))
            conn.commit()
        if rate != '':
            query = 'SELECT * FROM rate WHERE email=%s AND item_id=%s'
            cursor.execute(query, (email, item_id))
            result = cursor.fetchall()
            if len(result) == 0:
                query = 'INSERT INTO rate (email, item_id, rate_time, emoji) VALUES (%s, %s, NOW(), %s)'
                cursor.execute(query, (email, item_id, rate)) 
                conn.commit()
            else:
                query = 'UPDATE rate SET emoji=%s, rate_time=NOW() WHERE item_id=%s AND email=%s'
                cursor.execute(query, (rate, item_id, email))
                conn.commit()
        cursor.close()
        if rate == '' and comment=='':
            return render_template('rate_comment.html', error='Please rate or comment')
        else:
            return redirect(url_for('home'))
    except Exception as e:
        app.log_exception(e)
        return render_template('rate_comment.html', item_id=item_id)

@app.route('/tag')
def tag():
    return render_template('tag.html')

@app.route('/tagContent', methods=['POST'])
def tagContent():
    email = session['email']
    item_id = session['item_id']
    try:
        tagEmail = request.form['tagEmail']
        cursor = conn.cursor()
        if tagEmail == email:
            query = 'INSERT INTO tag (email_tagged, email_tagger, item_id, status) VALUES (%s, %s, %s, %s)'
            cursor.execute(query, (tagEmail, email, item_id, 'yes'))
            conn.commit()
            return render_template('tag.html', item_id=item_id)
        elif tagEmail != email:
            query = 'SELECT is_pub FROM ContentItem WHERE item_id = %s'
            cursor.execute(query, (item_id))
            result = cursor.fetchone()
            is_pub = result['is_pub']
            if is_pub:
                query = 'INSERT INTO tag (email_tagged, email_tagger, item_id, status) VALUES (%s, %s, %s, %s)'
                cursor.execute(query, (tagEmail, email, item_id, 'no'))
                conn.commit()
                return render_template('tag.html', item_id=item_id)
            else:
                query = 'SELECT email FROM belong WHERE fg_name IN (SELECT fg_name FROM share WHERE item_id = %s)'
                cursor.execute(query, (item_id))
                result = cursor.fetchall()
                if tagEmail in result:
                    query = 'INSERT INTO tag (email_tagged, email_tagger, item_id, status) VALUES (%s, %s, %s, %s)'
                    cursor.execute(query, (tagEmail, email, item_id, 'no'))
                    conn.commit()
                    return render_template('tag.html', item_id=item_id)

        cursor.close()
        return render_template('tag.html', item_id=item_id, error='Cannot propose tag')
    except Exception as e:
        app.log_exception(e)
        return render_template('tag.html', item_id=item_id, error='Cannot propose tag')


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)

# @app.route('/select_blogger')
# def select_blogger():
#     #check that user is logged in
#     #email = session['email']
#     #should throw exception if email not found

#     cursor = conn.cursor();
#     query = 'SELECT DISTINCT email FROM blog'
#     cursor.execute(query)
#     data = cursor.fetchall()
#     cursor.close()
#     return render_template('select_blogger.html', user_list=data)

# @app.route('/show_posts', methods=["GET", "POST"])
# def show_posts():
#     poster = request.args['poster']
#     cursor = conn.cursor();
#     query = 'SELECT ts, blog_post FROM blog WHERE email = %s ORDER BY ts DESC'
#     cursor.execute(query, poster)
#     data = cursor.fetchall()
#     cursor.close()
#     return render_template('show_posts.html', poster_name=poster, posts=data)

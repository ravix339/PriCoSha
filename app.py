#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
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

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

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

@app.route('/home')
def home():
    cursor = conn.cursor();
    query = 'SELECT post_time, item_id, email_post, file_path, item_name FROM ContentItem WHERE is_pub = %s or is_pub is NULL AND post_time >= DATE_SUB(NOW(), INTERVAL 1 DAY) ORDER BY post_time DESC'
    cursor.execute(query, (0))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', email=session['email'], posts=data)

@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)


# #Authenticates the register
# @app.route('/registerAuth', methods=['GET', 'POST'])
# def registerAuth():
#     #grabs information from the forms
#     email = request.form['email']
#     password = request.form['password']

#     #cursor used to send queries
#     cursor = conn.cursor()
#     #executes query
#     query = 'SELECT * FROM user WHERE email = %s'
#     cursor.execute(query, (email))
#     #stores the results in a variable
#     data = cursor.fetchone()
#     #use fetchall() if you are expecting more than 1 data row
#     error = None
#     if(data):
#         #If the previous query returns data, then user exists
#         error = "This user already exists"
#         return render_template('register.html', error = error)
#     else:
#         ins = 'INSERT INTO user VALUES(%s, %s)'
#         cursor.execute(ins, (email, password))
#         conn.commit()
#         cursor.close()
#         return render_template('index.html')


# @app.route('/post', methods=['GET', 'POST'])
# def post():
#     email = session['email']
#     cursor = conn.cursor();
#     blog = request.form['blog']
#     query = 'INSERT INTO blog (blog_post, email) VALUES(%s, %s)'
#     cursor.execute(query, (blog, email))
#     conn.commit()
#     cursor.close()
#     return redirect(url_for('home'))

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

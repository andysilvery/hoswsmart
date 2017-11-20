from flask import Flask, render_template, flash, redirect, url_for, session,request, logging  
#from data import Articles  
from flask_mysqldb import MySQL 
from wtforms import Form, StringField, TextAreaField, PasswordField,validators 
from passlib.hash import sha256_crypt 
from functools import wraps
app =  Flask(__name__) 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root' 
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'myflaskapp' 
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

MariaDB = MySQL(app)
#Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/article/<string:id>/')
def article(id):
    cur = MariaDB.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])

    article =  cur.fetchone()
    return render_template('article.html', article=article)

@app.route('/about')
def about():
    return render_template('about.html')

class RegisterForm(Form):
    name = StringField('Name', validators=[validators.input_required()])
    username  = StringField('Username', validators=[validators.optional()])
    email = StringField('Email ' , [validators.Length(min=6, max=80)])
    password=PasswordField('Password', [validators.DataRequired(),validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password',)
                           
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))
        cur=MariaDB.connection.cursor()
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)", (name,email,username,password))
    # connect to DB
        MariaDB.connection.commit()
        # close connection
        cur.close()
        
        flash("Thank you for registering , you will be able to login and check yout status")
        
        return redirect(url_for('login'))
                           
    return render_template('register.html', form = form)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        cur=MariaDB.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username = %s",[username])
        
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in'] =  True
                session['username'] = username
                
                flash("You are signed in ", "success")
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid credentials'
                return render_template('login.html', error=error)
            cur.close()  
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Login to access','danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/articles')
@is_logged_in
def articles():
    
    cur = MariaDB.connection.cursor()
    username = session['username']

    result = cur.execute("SELECT * FROM articles WHERE author = %s",[username])

    #result = cur.execute("SELECT * FROM articles")

    articles =  cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg=msg) 


        cur.close()   

    return render_template('articles.html', articles = articles)


@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = MariaDB.connection.cursor()
    username = session['username']

    result = cur.execute("SELECT * FROM articles WHERE author = %s",[username])
    #result = cur.execute("SELECT * FROM articles ")

    articles =  cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg) 


        cur.close()   



    return render_template('dashboard.html')


	
class ArticleForm(Form):
		title = StringField('Title', [validators.Length(min=1, max=200)])
		body = TextAreaField('Body', [validators.Length(min=30)])
	
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        cur = MariaDB.connection.cursor()
        cur.execute("INSERT INTO articles(title, body, author) VALUES ( %s, %s, %s)", (title, body, session['username']))
	    
        MariaDB.connection.commit()
	    
        cur.close()
		
        flash('Article Create', ' success')
	    
        return redirect(url_for('dashboard'))


	

    return render_template('add_article.html',  form= form)

@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    cur = MariaDB.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id = %s ", [id])
    
    article  = cur.fetchone()
      
    form = ArticleForm(request.form)
    
    form.title.data = article['title']
    
    form.body.data = article['body']
    #corrected till here
    
    if request.method == 'POST' and form.validate():
        title = request.form['title']
    
        body = request.form['body']
    
        cur = MariaDB.connection.cursor()
    
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body,id))
    
        MariaDB.connection.commit()
    
        cur.close()
    
        flash('Article updated', 'success')
    
        return redirect(url_for('dashboard'))
    
    return render_template('edit_article.html',  form= form)

@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):

    cur = MariaDB.connection.cursor()

    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    MariaDB.connection.commit()

    cur.close()

    flash('Artile Deleted', 'success')

    return redirect(url_for('dashboard'))


if  __name__ == '__main__':
    app.secret_key="secret123"
    app.run(debug=True)
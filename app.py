from logging import INFO
from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback
from forms import UserForm, LoginForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
toolbar = DebugToolbarExtension(app)

@app.route('/')
def home():
    return redirect('/register')

@app.route('/register', methods=["GET","POST"])
def register():
    if "username" in session:
        username = session['username']
        flash('You are already registered.', 'info')
        return redirect(f'/users/{username}')
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username,password,email,first_name,last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except:
            flash('Username or Email is already existed','danger')
            return render_template('register.html', form=form)
        session['username'] = new_user.username
        flash('Successfully created your account!', 'success')
        return redirect(f'/users/{username}')

    return render_template('register.html',form=form)

@app.route('/users/<username>')
def user_page(username):
    if "username" not in session:
        flash('Please login first!','danger')
        return redirect('/login')
    user = User.query.get_or_404(username)
    feedbacks = Feedback.query.filter_by(username=username).all()
    return render_template('user.html',user=user, feedbacks=feedbacks)

@app.route('/users/<username>/delete', methods=["POST"])
def delete_user(username):
    if "username" not in session:
        flash('Please login first!','danger')
        return redirect('/login')
    user = User.query.get_or_404(username)
    feedbacks = user.feedbacks

    for feedback in feedbacks:
        db.session.delete(feedback)
    db.session.delete(user)
    db.session.commit()
    flash('Deleted a user','info')
    return redirect('/')

@app.route('/login', methods=["GET","POST"])
def login():
    if "username" in session:
        username = session['username']
        flash('You are already logged in.', 'info')
        return redirect(f'/users/{username}')
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username,password)
        if user:
            session['username'] = user.username
            flash(f'Hello, {user.username}!','success')
            return redirect(f'/users/{username}')
        else:
            flash("Invalid username or password",'danger')
            return render_template('login.html',form=form)
    
    return render_template('login.html',form=form)

@app.route('/logout')
def logout():
    session.pop('username')
    flash('Goodbye!','info')
    return redirect('/')
from logging import INFO
from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm

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
    if "username" in session:
        username = session['username']
        return redirect(f'/users/{username}')
    return render_template('index.html')

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

@app.route('/users/<username>')
def user_page(username):
    if "username" not in session:
        flash('Please login first!','danger')
        return redirect('/login')
    if session['username'] != username:
        flash("You are not authorize to view this user page.",'danger')
        return redirect('/')
    user = User.query.get_or_404(username)
    feedbacks = Feedback.query.filter_by(username=username).all()
    return render_template('user.html',user=user, feedbacks=feedbacks)

@app.route('/users/<username>/feedback/add', methods=["GET","POST"])
def user_feedback(username):
    """Go to feedback form and Post feedback"""
    if "username" not in session:
        flash("Please login first!", 'danger')
        return redirect('/')
    if session['username'] != username:
        flash("You are not authorize to post feedbacks to this user page.",'warning')
        return redirect('/')
    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title=title, content=content,username=session['username'])
        db.session.add(feedback)
        db.session.commit()
        flash("Feedback Created!", 'success')
        return redirect(f'/users/{username}')

    return render_template('feedback.html', form=form)

@app.route('/feedback/<int:id>/update', methods=["GET","POST"])
def feedback_update(id):
    """Update a feedback"""
    feedback = Feedback.query.get_or_404(id)
    username = feedback.user.username
    if "username" not in session or session['username'] != username:
        flash("You are not authorize to update this feedback", 'warning')
        return redirect('/')

    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback.title = title
        feedback.content = content
        db.session.add(feedback)
        db.session.commit()
        flash("Feedback Updated!", 'success')
        return redirect(f'/users/{username}')
    
    return render_template('feedback.html', form=form)

@app.route('/feedback/<int:id>/delete', methods=["POST"])
def delete_feedback(id):
    """delete a feedback"""
    feedback = Feedback.query.get_or_404(id)
    username = feedback.user.username
    if "username" not in session or session['username'] != username:
        flash("You are not authorize to delete this feedback", 'warning')
        return redirect('/')
    else:
        db.session.delete(feedback)
        db.session.commit()
        flash('Feedback deleted!', 'info')
        return redirect(f'/users/{username}')

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
    session.pop('username')
    flash('Deleted a user, Goodbye','info')
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('username')
    flash('Goodbye!','info')
    return redirect('/')
import os
from dotenv import load_dotenv
import datetime
from bson import ObjectId
import pymongo
import flask_login
from flask import Flask, render_template, request, session, redirect, url_for, flash
# from passlib.hash import pbkdf2_sha256


# load in the variables in the .env file into our operating system environment
load_dotenv()

app = Flask(__name__)

# connect to mongo
MONGO_URI = os.environ.get('MONGO_URI')
client = pymongo.MongoClient(MONGO_URI)

# define my db_name
DB_NAME = os.environ.get('DB_NAME')
USER_COLLECTION_NAME = os.environ.get('USER_COLLECTION_NAME')

# read in the SESSION_KEY variable from the operating system environment
SESSION_KEY = os.environ.get('SESSION_KEY')

# set the session key
app.secret_key = os.environ.get('SESSION_KEY')

# --- User Authentication: Start  ----------------------------
# create a login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# User object
# This user object basically represents one user


class User(flask_login.UserMixin):
    pass


# user loader for the Flask-Login login manager
@login_manager.user_loader
def load_user(email):
    # find the user from the database by its email
    user_data = client[DB_NAME][USER_COLLECTION_NAME].find_one({
        'email': email
    })
    if user_data:
        # create a new user object
        current_user = User()
        current_user._id = str(user_data['_id'])
        current_user.id = user_data['email']
        current_user.email = user_data['email']
        current_user.nickname = user_data['nickname']
        current_user.admin = user_data['admin']
        return current_user
    else:
        return None


# encrypt user's password        <-- rmb to use your database to create a collection that stores registered users' info like passwords and emails
def password_encryptor(user_password):
    return pbkdf2_sha256.hash(user_password)

# verify user's password        <-- then use this function to check user's password against the password in your collection


def verify_password(user_input, encrypted_password):
    return pbkdf2_sha256.verify(user_input, encrypted_password)

# --- User Authentication: End ---------------------------------

# START ROUTING
@app.route('/')
def index():
    return redirect(url_for("home"))

# a list random 5 articles
# list all
# search panel: search by article title, cleaning location and tags
# search result return in a list of title, cleaning location
# click on list to view article

@app.route('/home')
def home():
    return render_template("home.template.html")

# --------------------------------------------------
# Login
# --------------------------------------------------
# Login Page
# accept email address and password
# successful verification will be shown a login successful message
# and redirect to home.
# unsuccessful verificaiton will be shown relevant error message
# and ask to retry


@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # recieved as form submitted
        form = request.form
        current_user = load_user(form.get('input-email'))
        if load_user(form.get('input-email')) is None:
            # no such email exist in database
            flash("User not found", category='danger')
            return render_template("/auth/login.template.html", form=form)
        else:
            # email found in database, check password
            user_data = client[DB_NAME][USER_COLLECTION_NAME].find_one({
                'email': form.get('input-email'),
                'password': form.get('input-password')}
            )
            if user_data is None:
                # password incorrect
                flash('Password incorrect.', 'danger')
                return render_template("/auth/login.template.html", form=form)
            else:
                # password correct
                flask_login.login_user(current_user)
                flash(current_user.nickname +
                      ' logged in successfully.', 'success')
                session['id'] = current_user.id
                session['email'] = current_user.email
                session['nickname'] = current_user.nickname
                session['admin'] = current_user.admin
                return redirect(url_for('home'))
    else:
        # This template shows a login form,
        # only called if the request.method was not 'POST'.
        return render_template("/auth/login.template.html")


@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    return render_template("/unauthorized.template.html")


# --------------------------------------------------
# Logout
# --------------------------------------------------
# A instruction to log the user out and return to the home page
@app.route('/auth/logout')
def logout():
    current_user = flask_login.current_user
    flash(session['nickname']+' logged out successfully.', 'success')
    flask_login.current_user = User
    session.pop('email', None)
    session.pop('nickname', None)
    session.pop('admin', None)
    flask_login.logout_user()
    return redirect(url_for('home'))

# Registration form
# Allow an user to register for an account
# Redirect to login page after successful registration


@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form
        # check whether the passwords are the same
        if not(form.get('input-password') == form.get('input-verify')):
            flash("The passwords do not match. Please retry.",
                  category='danger')
            return render_template("/auth/register.template.html", form=form)
        else:
            # check whether email is unique
            user_data = client[DB_NAME][USER_COLLECTION_NAME].find_one({
                'email': form.get('input-email')
            })
            if user_data:
                # Email address found in the database
                flash(
                    "This email address has been used for registration. " +
                    "Please use other email address", category='danger')
                return render_template("/auth/register.template.html",
                                       form=form)
            else:
                user_data = client[DB_NAME][USER_COLLECTION_NAME].insert_one({
                    'email': form.get('input-email'),
                    'nickname': form.get('input-nickname'),
                    'password': form.get('input-password'),
                    'admin': False}
                )
                flash("User registration successful. Please proceed to login.",
                      category='success')
                return render_template("/auth/login.template.html")
    else:
        # register form
        return render_template("/auth/register.template.html")


# --------------------------------------------------
# My Profile
# --------------------------------------------------
# Allow the user to view their own profile
# and update their nickanme and password
@app.route('/users/my-profile', methods=['GET', 'POST'])
@ flask_login.login_required
def my_profile():
    if request.method == 'POST':
        form = request.form
        print(form)
        if form.get('input-password') == "":
            # no change in password, direct update nickname
            myquery = {'email': form.get('input-email')}
            updatevalues = {'$set': {'nickname': form.get('input-nickname')}}
            client[DB_NAME][USER_COLLECTION_NAME].update_one(
                myquery, updatevalues)
            flash("Profile successfully updated", category='success')
            return render_template("/users/my-profile.template.html",
                                   form=form)
        else:
            # changes to passowrd, to check both passwods to be the same
            # if both password are not the same
            if not(form.get('input-password') == form.get('input-verify')):
                # if the two passwords are not the same
                flash("The passwords do not match. Please retry.",
                      category='danger')
                return render_template("/users/my-profile.template.html",
                                       form=form)
            else:
                myquery = {'email': form.get('input-email')}
                updatevalues = {'$set': {'nickname': form.get(
                    'input-nickname'), 'password': form.get('input-password')}}
                client[DB_NAME][USER_COLLECTION_NAME].update_one(
                    myquery, updatevalues)
                flash("Profile successfully updated", category='success')
                return render_template("/users/my-profile.template.html",
                                       form=form)
    else:
        return render_template("/users/my-profile.template.html")


@ app.route('/about')
def about():
    return render_template("/about.template.html")


@ app.route('/instructions')
def instructions():
    return render_template("/instructions.template.html")


# Allow user to select one of the articles by clicking
#  on the article titles from the search results
#  to view the article.
# Allow user to select one of the articles by clicking on
# the article titles from the list to view the article.
# Allow member to select one of the articles by clicking on
# the article titles from the list to view the article.
# Allow member to select one of the articles by clicking on
# the corresponding delete button.
# Allow member to delete the article by clicking on the
# delete confirmation button on the article itself.
# When a search is executed, it will return the result
# in a list containing article titles and cleaning locations.
# Allow administrator to select one of article by clicking
# on the article titles from the search results to view the article.
# Allow administrator to delete an article by clicking on the corresponding delete button.
# Allow administrator to delete any article.
@ app.route('/articles/list')
def list_articles():
    return render_template("/articles/article-list.template.html")


# Display the article containing article titles,
# cleaning location, article content, cleaning items,
# cleaning supplies and tags.
# List the comments for individual articles
# Display the count of validating vote.
# Allow member to edit the article by clicking on the
# edit button on the article itself.
# Allow member to add a comment on the article page.
# Allow member to edit the comment he left
# on the article page
# Allow member to validate the article content by voting
# whether it works, somewhat works, or doesn’t work.
# Allow member to change their validating votes.
# Allow member to edit articles they contributed.
# Allow member to delete articles they contributed.
# Allow administrator to delete an article by clicking on the delete button on the article itself.
# Allow administrator to edit an article by clicking on the edit button on the article itself.
# Allow administrator to add a comment on the article page.
# Allow member to edit the comment he left on the article page.
# Allow administrator to validate the article content by voting
#  whether it works, somewhat works, or doesn’t work.
# Allow administrator to change their validating votes.
# Allow administrator to edit any article.
@ app.route('/articles/show/<id>')
def show_article(id):
    return render_template("/articles/article.template.html", id=id)


# Display a list of all articles the member contributed.
# Allow member to select one of the articles by clicking on
# the article titles from the list to view the article.
# Allow member to select one of the articles by clicking on
# the corresponding delete button.
# Allow member to delete the article by clicking on the
# delete confirmation button on the article itself.
# Allow administrator to select one of article by clicking
# on the article titles from the search results to view the article.
# Allow administrator to delete an article by clicking on the corresponding delete button.
# Allow administrator to delete any article.
@ app.route('/articles/my-list')
@ flask_login.login_required
def my_articles():
    return render_template("/articles/my-list.template.html")

# Include an article creation page accepting article titles,
# cleaning location, article content, cleaning items,
# cleaning supplies and tags.
# Include an article creation page accepting article titles,
#  cleaning location, article content, cleaning items, cleaning supplies and tags.


@ app.route('/articles/contribute')
@ flask_login.login_required
def contribute_articles():
    return render_template("/articles/contribute.template.html")


# --------------------------------------------------
# Cleaning Locations
# --------------------------------------------------
# Allow administrator to manage the list of cleaning location.
@ app.route('/cleaning-locations/manage', methods=['GET', 'POST'])
@ flask_login.login_required
def manage_cleaning_locations():
    if request.method == 'POST':
        form = request.form
        location_data = client[DB_NAME]['cleaning_locations'].find_one(
            {'_id': ObjectId(form.get('id'))})
        # render a form to allow editing of the selectedd cleaning location
        if form.get('action') == "edit":
            return render_template("/cleaning-locations/edit.template.html",
                                   location_data=location_data)
        # update the database with the changes to
        # the selected cleaning location
        elif form.get('action') == "edit-process":
            myquery = {'_id': ObjectId(form.get('id'))}
            updatevalues = {'$set': {'location': form.get('input-location')}}
            client[DB_NAME]['cleaning_locations'].update_one(
                myquery, updatevalues)
            flash('Location successfully updated', category='success')
            return redirect("/cleaning-locations/manage")
        # display the record mark for deletion to ask for confirmation
        elif form.get('action') == "delete":
            return render_template("/cleaning-locations/delete.template.html",
                                   location_data=location_data)
        # remove the selected clearning location from the database
        elif form.get('action') == "delete-process":
            myquery = {'_id': ObjectId(form.get('id'))}
            client[DB_NAME]['cleaning_locations'].delete_one(myquery)
            flash('Location successfully deleted', category='success')
            return redirect("/cleaning-locations/manage")
        # Insert the new cleaning location into the database
        elif form.get('action') == "add":
            client[DB_NAME]['cleaning_locations'].insert_one(
                {'location': form.get('input-new-location')})
            flash("New cleaning location added.")
            return redirect("/cleaning-locations/manage")
        else:
            return redirect(url_for('error_encountered'))
    else:
        # display the add cleaning location form and
        # list out the cleaning locations in the databasse
        location_data = client[DB_NAME]['cleaning_locations'].find().sort(
            'location', pymongo.ASCENDING)
        return render_template("/cleaning-locations/manage.template.html",
                               location_data=location_data)

# --------------------------------------------------
# Users Administration
# --------------------------------------------------
# Allow administrators to manage the list of users.


@ app.route('/users/manage', methods=['GET', 'POST'])
@ flask_login.login_required
def manage_users():
    if request.method == 'POST':
        form = request.form
        user_data = client[DB_NAME][USER_COLLECTION_NAME].find_one(
            {'_id': ObjectId(form.get('id'))})
        # Render a form to allow editing of the selected user
        # This includes changing nickname, reset password and
        # assigning administrator's rights
        if form.get('action') == 'edit':
            return render_template("/users/edit.template.html",
                                   form=form, user_data=user_data)
        # update the database with the changes to the selected user
        elif form.get('action') == 'edit-process':
            if form.get('input-password') == "":
                if form.get('input-admin') == 'isAdmin':
                    adminrights = True
                else:
                    adminrights = False
                # no change in password, direct update nickname and/or admin
                myquery = {'_id': ObjectId(form.get('id'))}
                updatevalues = {'$set': {'nickname': form.get(
                    'input-nickname'), 'admin': adminrights}}
                client[DB_NAME][USER_COLLECTION_NAME].update_one(
                    myquery, updatevalues)
                flash("User details successfully updated", category='success')
                return render_template("/users/edit.template.html",
                                       form=form, user_data=user_data)
            else:
                if not(form.get('input-password') == form.get('input-verify')):
                    flash("The passwords do not match. Please retry.",
                          category='danger')
                    return render_template("/users/edit.template.html",
                                           form=form, user_data=user_data)
                else:
                    myquery = {'_id': ObjectId(form.get('id'))}
                    if form.get('input-admin') == 'isAdmin':
                        adminrights = True
                    else:
                        adminrights = False
                    updatevalues = {'$set': {
                        'nickname': form.get('input-nickname'),
                        'password': form.get('input-password'),
                        'admin': adminrights}}
                    client[DB_NAME][USER_COLLECTION_NAME].update_one(
                        myquery, updatevalues)
                    flash("Profile successfully updated", category='success')
                    return render_template("/users/edit.template.html",
                                           form=form, user_data=user_data)
        # display the record mark for deletion to ask for confirmation
        elif form.get('action') == 'delete':
            return render_template("/users/delete.template.html",
                                   form=form, user_data=user_data)
        # remove the selected user from the database
        elif form.get('action') == "delete-process":
            myquery = {'_id': ObjectId(form.get('id'))}
            client[DB_NAME][USER_COLLECTION_NAME].delete_one(myquery)
            flash('User successfully deleted', category='success')
            return redirect("/users/manage")
        else:
            return redirect(url_for('error_encountered'))
    else:
        # display the search box and list out the users in the databasse
        user_data = client[DB_NAME][USER_COLLECTION_NAME].find().sort(
            'nickname', pymongo.ASCENDING)
        return render_template("/users/manage.template.html",
                               user_data=user_data)


# inbuilt function which handles exception like file not found
@ app.errorhandler(404)
def not_found(e):
    return render_template('/file-not-found.template.html')


@ app.route('/error-encountered')
def error_encountered():
    return render_template('/error-encountered.template.html')


# "magic code" -- boilerplate
if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)

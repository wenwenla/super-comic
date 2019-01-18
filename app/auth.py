from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from app.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('POST', 'GET'))
def register():
    # if request.method == 'POST':
    # return render_template('auth/register.html')
    return render_template('404.html')


@bp.route('/login', methods=('POST', 'GET'))
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = User.query.filter_by(name=name).first()
        error = None
        if name is None:
            error = 'Name is required'
        elif password is None:
            error = 'Password is required'
        elif user is None:
            error = 'No such user'
        elif user.password != password:
            error = 'Wrong password'
        else:
            session['user_id'] = user.id
        if not error:
            return redirect(url_for('comic.list_'))
        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

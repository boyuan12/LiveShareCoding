from functools import wraps
from flask import session, request, redirect, url_for
from string import ascii_letters, digits
import random


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function



def random_str(n=6):
    string = ""
    for i in range(n):
        string += random.choice(ascii_letters + digits)
    return string

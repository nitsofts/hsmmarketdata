from flask import Blueprint, request, abort
from config import API_KEY  # Import API_KEY from config.py

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    api_key = request.args.get('api_key')
    if api_key == API_KEY:
        return "Thanks for visiting! Your IP has been recorded."
    else:
        abort(401)

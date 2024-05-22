import logging
from flask import Flask
from config import API_KEY
from routes.home import home_bp
from routes.top_performers import top_performers_bp
from routes.prospectus import prospectus_bp
from routes.cdsc_data import cdsc_data_bp
from routes.market_indices import market_indices_bp
from routes.upcoming_issues import upcoming_issues_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

app.register_blueprint(home_bp)
app.register_blueprint(top_performers_bp)
app.register_blueprint(prospectus_bp)
app.register_blueprint(cdsc_data_bp)
app.register_blueprint(market_indices_bp)
app.register_blueprint(upcoming_issues_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

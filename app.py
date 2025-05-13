from flask import Flask
from flask_cors import CORS  # Add this
import logging

from config import API_KEY
from routes.home import home_bp
from routes.auto_post import auto_post_bp
from routes.top_performers import top_performers_bp
from routes.prospectus import prospectus_bp
from routes.cdsc_data import cdsc_data_bp
from routes.market_indices import market_indices_bp
from routes.upcoming_issues import upcoming_issues_bp
from routes.stock_movement_summary import stock_movement_summary_bp
from routes.market_insights import market_insights_bp
from routes.watchlist import watchlist_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ✅ Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Or set a specific origin like "https://hamrosharemarket.com"

# Register all blueprints
app.register_blueprint(home_bp)
app.register_blueprint(auto_post_bp, url_prefix='/api')
app.register_blueprint(top_performers_bp)
app.register_blueprint(prospectus_bp)
app.register_blueprint(cdsc_data_bp)
app.register_blueprint(market_indices_bp)
app.register_blueprint(upcoming_issues_bp)
app.register_blueprint(stock_movement_summary_bp)
app.register_blueprint(market_insights_bp, url_prefix='/api')
app.register_blueprint(watchlist_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

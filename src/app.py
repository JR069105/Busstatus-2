from flask import jsonify, Flask, render_template, url_for, abort
from src.scrape import scrape_data
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

scheduler = BackgroundScheduler()

if 'SENTRY_URL' in os.environ:
    sentry_sdk.init(
        dsn=os.environ['SENTRY_URL'],
        integrations=[FlaskIntegration()],
    
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.0
    )

app = Flask(__name__, static_folder='../static', static_url_path='/static',
template_folder='../templates')

def formatTimestamp(timestamp):
    return timestamp.strftime('%A %m/%d/%Y %H:%M:%S')
    
def update_data():
    global bus_data
    
    bus_data = scrape_data()
    print(f"Data updated at {datetime.now()}")

@app.before_first_request
def setup_scrapes():
    update_data()
    job = scheduler.add_job(update_data, 'interval', minutes=1)
    scheduler.start()

@app.route("/")
def home_page():
    return render_template('index.html', schools=bus_data["schools"], last_updated=formatTimestamp(bus_data["last_updated"]))
    
@app.route("/json")
def raw():
    return jsonify(bus_data)
    
@app.route("/debug")
def trigger_error():
    result = 1 / 0
    
@app.route("/scrape")
def scrape():
    bus_data = scrape_data()
    return "Successful", 200
    
@app.route("/<schoolname>")
def school_page(schoolname):
    if schoolname not in bus_data["data"]:
        abort(404)
    return render_template('school.html', data=bus_data["data"][schoolname], last_updated=formatTimestamp(bus_data["last_updated"]), school=bus_data["reverse_schools"][schoolname])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050)
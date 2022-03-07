from flask import jsonify, Flask, render_template, url_for, abort
from src.scrape import scrape_data

app = Flask(__name__, static_folder='../static', static_url_path='/static',
template_folder='../templates')

@app.before_first_request
def initial_scrape():
    global bus_data
    
    bus_data = scrape_data()

@app.route("/")
def home_page():
    return render_template('index.html', schools=bus_data["schools"])
    
@app.route("/json")
def raw():
    return jsonify(bus_data)
    
school_headers = {"morning": "Morning Cancellations", "afternoon": "Afternoon Cancellations", "changes": "Changes"}
@app.route("/<schoolname>")
def school_page(schoolname):
    if schoolname not in bus_data["data"]:
        abort(404)
    return render_template('school.html', data=bus_data["data"][schoolname], school_headers=school_headers, school=bus_data["reverse_schools"][schoolname])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050)
from flask import *
import scraper

app = Flask(__name__)
app.secret_key = 'cool_key'  # Set a unique and secret key

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Capture form data
        username = request.form.get('username')
        password = request.form.get('password')
        lists = request.form.get('lists')

        # Call the scraper function with the collected data
        status = scraper.scrape(username, password, lists)

        if status == 'success':
            flash('Scraper successful!')
        else:
            flash('Scraper failed. Try running the program again. If that does not work, contact Ethan or Joel.')

        # Redirect to index after processing
        return redirect(url_for('index'))

        # Render the index page for GET requests
    return render_template("index.html")


if __name__ == '__main__':
    app.run()
from flask import Flask, request, render_template, redirect, url_for, flash
import scraper

app = Flask(__name__)
app.secret_key = 'cool_key'  # Set a unique and secret key


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Capture form data with validation
        username = request.form.get('username')
        if not username:
            flash('You must enter your username!')
            return render_template("index.html")

        password = request.form.get('password')
        if not password:
            flash('You must enter your password!')
            return render_template("index.html")

        lists = request.form.get('lists')
        if lists:
            # Clean and split the lists input
            loop_lists = [item.strip() for item in lists.split(',')]
            #print(loop_lists)
        else:
            loop_lists = []

        # Call the scraper function with the collected data
        status = scraper.scrape(username, password, loop_lists)

        # Handle the scraper result
        if status == 'success':
            flash('Scraper successful! File is saved to your downloads folder.')
        else:
            flash('Scraper failed. Try running the program again. If that does not work, contact Ethan or Joel.')

        # Redirect to index after processing
        return redirect(url_for('index'))

    # Render the index page for GET requests
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)  # Enable debug mode for development

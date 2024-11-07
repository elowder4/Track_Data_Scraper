import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout
import multiprocessing
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QMovie, QFontMetrics
import scraper


# Function to run the scraper in a separate process
def run_scraper(email, password, lists, queue):
    # Run the scraper function and put the result in the queue
    status = scraper.scrape(email, password, lists)
    queue.put(status)  # Send the status back to the main process


def create_gui():
    # Create application's GUI
    window = QWidget()
    window.setWindowTitle("Track Data Scraper")
    window.setGeometry(100, 100, 800, 300)

    # Create layout
    layout = QVBoxLayout()  # Stack widgets

    # Add title
    header = QLabel("<h1>Get Ready to Scrape!</h1>")
    layout.addWidget(header)

    # Add three input fields
    email = QLineEdit()
    email.setPlaceholderText("Email")
    layout.addWidget(email)

    password = QLineEdit()
    password.setPlaceholderText("Password")
    layout.addWidget(password)

    lists = QLineEdit()
    lists.setPlaceholderText("Lists to Scrape (list name 1, list name 2, etc.)")
    layout.addWidget(lists)

    # Create a button to process inputs
    submit_button = QPushButton("Submit")
    layout.addWidget(submit_button)

    # Create a horizontal layout for result and loading spinner
    result_layout = QHBoxLayout()

    # Create a label to show the result
    result_label = QLabel("")
    result_layout.addWidget(result_label)

    # Create a label for the loading spinner
    loading_label = QLabel("")
    loading_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align left
    loading_label.setFixedSize(19, 19)  # Set fixed size for the loading label
    loading_label.setScaledContents(True)  # Allow scaling of the content
    result_layout.addWidget(loading_label)

    # Create a label for the success indicator
    status_label = QLabel("")
    status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Align left
    status_label.setScaledContents(True)  # Allow scaling of the content

    # Add the result and status layout to the main layout
    layout.addLayout(result_layout)
    layout.addWidget(status_label)

    # Handle the button click
    def on_submit():
        # Get the text from the input fields
        value1 = email.text()
        value2 = password.text()
        value3 = lists.text()

        # Check if username or password are empty
        if not value1 or not value2:
            # Show a warning message box
            QMessageBox.warning(window, "Input Error", "Email and Password Required!", QMessageBox.StandardButton.Ok)
            return  # Exit the function if inputs are not valid

        result_label.setText('Scraper is working. Please wait. This will take 2-20 minutes. BE PATIENT!')
        loading_label.clear()  # Clear the loading label initially
        status_label.clear()

        # Create and start the loading animation
        movie = QMovie("gif/loading.gif")  # Load GIF file
        loading_label.setMovie(movie)
        movie.start()  # Start the animation

        # Resize the loading label to match the text height of result_label
        metrics = QFontMetrics(result_label.font())
        text_height = metrics.height()  # Get the height of the text
        loading_label.setFixedHeight(text_height)  # Set loading label height to match text height

        # Create a Queue to receive results from the subprocess
        queue = multiprocessing.Queue()

        # Create a new process to run the scraper
        process = multiprocessing.Process(target=run_scraper, args=(value1, value2, value3, queue))
        process.start()

        # Check for results while the process is running
        def check_for_result():
            if not queue.empty():
                status = queue.get()  # Get the result from the queue
                process.join()  # Wait for the process to finish

                # Update the result label based on the status
                if status == 'success':
                    loading_label.clear()
                    result_label.setText('Scraper successful! File is saved to your downloads folder.')
                    # Create and start the loading animation
                    success = QMovie("gif/success.gif")  # Load GIF file
                    status_label.setMovie(success)
                    success.start()  # Start the animation
                else:
                    loading_label.clear()
                    result_label.setText('Scraper failed. Check your inputs and try again. If the program continues to fail, contact Ethan.')
                    # Create and start the loading animation
                    failure = QMovie("gif/failure.gif")  # Load GIF file
                    status_label.setMovie(failure)
                    failure.start()  # Start the animation

            else:
                # If the queue is still empty, check again after 100 ms
                QTimer.singleShot(100, check_for_result)

        check_for_result()  # Start checking for results

    # Connect the button's clicked signal to the on_submit function
    submit_button.clicked.connect(on_submit)

    # Set the layout to the window
    window.setLayout(layout)

    return window


# Create an instance of QApplication and show the GUI (prevents multiple windows from opening)
if __name__ == '__main__':
    app = QApplication([])

    # Create the main window
    window = create_gui()

    # Show your application's GUI
    window.show()

    # Run application's event loop
    sys.exit(app.exec())

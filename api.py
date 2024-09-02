from flask import Flask, request, redirect, url_for, flash, render_template_string
import subprocess
import re

app = Flask(__name__)
app.secret_key = '2a9d4eb186c27f03671e0374db94a648'  # Replace with a secure key for production

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hotel Scraper Scheduler</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body {
            background-image: url('https://images.unsplash.com/photo-1564866659-cd49f94c74ed?fit=crop&w=1920&h=1080');
            background-size: cover;
            background-attachment: fixed;
            color: #fff;
        }
        .container {
            background-color: rgba(0, 0, 0, 0.7);
            padding: 30px;
            border-radius: 10px;
            margin-top: 50px;
        }
        .form-control {
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .btn-info {
            background-color: #17a2b8;
            border-color: #17a2b8;
            border-radius: 5px;
        }
        .btn-info:hover {
            background-color: #138496;
            border-color: #117a8b;
        }
        .alert {
            margin-top: 20px;
        }
        .spinner-border {
            display: none;
            margin-top: 20px;
        }
        .custom-tooltip .tooltip-inner {
            background-color: #333;
            color: #fff;
            border-radius: 5px;
        }
        .custom-tooltip .tooltip-arrow {
            border-top-color: #333;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">Hotel Scraper Scheduler</h1>

        <!-- Display Flash Messages -->
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="alert alert-info" role="alert">
                    {{ messages[0] }}
                </div>
            {% endif %}
        {% endwith %}

        <form id="scheduler-form" method="post">
            <div class="form-group">
                <label for="cities">Add Cities (one per line):</label>
                <textarea class="form-control" id="cities" name="cities" rows="5" placeholder="Enter cities here..."></textarea>
                <div id="cities-error" class="text-danger" style="display: none;">Please enter at least one city.</div>
            </div>
            <div class="form-group">
                <label for="time">Enter Time (HH:MM):</label>
                <input type="text" class="form-control" id="time" name="time" placeholder="Enter time here..." />
                <div id="time-error" class="text-danger" style="display: none;">Invalid time format. Please enter in HH:MM format.</div>
            </div>
            <button type="submit" class="btn btn-info" 
                    data-bs-toggle="tooltip" data-bs-placement="top"
                    data-bs-custom-class="custom-tooltip"
                    data-bs-title="Click to save cities and time, then start scraping.">
                Save and Start Scraping
            </button>
        </form>

        <div id="spinner-container" class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>  
    </div>

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script>
        // Initialize tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        });

        document.getElementById('scheduler-form').addEventListener('submit', function(event) {
            var timeInput = document.getElementById('time').value;
            var citiesInput = document.getElementById('cities').value;
            var timeError = document.getElementById('time-error');
            var citiesError = document.getElementById('cities-error');
            var timePattern = /^([01]\d|2[0-3]):([0-5]\d)$/;

            var valid = true;

            if (!timePattern.test(timeInput)) {
                timeError.style.display = 'block';
                valid = false;
            } else {
                timeError.style.display = 'none';
            }

            if (!citiesInput.trim()) {
                citiesError.style.display = 'block';
                valid = false;
            } else {
                citiesError.style.display = 'none';
            }

            if (!valid) {
                event.preventDefault(); // Prevent form submission
            } else {
                document.getElementById('spinner-container').style.display = 'block';
            }
        });
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cities = request.form.get('cities')
        time = request.form.get('time')

        # Server-side validation for time format and empty fields
        time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
        if not cities or not time:
            flash('Please enter both cities and time.')
            return redirect(url_for('index'))
        elif not time_pattern.match(time):
            flash('Invalid time format. Please enter in HH:MM format.')
            return redirect(url_for('index'))

        # Save inputs to files
        with open('city.txt', 'w') as city_file:
            city_file.write(cities)

        with open('time.txt', 'w') as time_file:
            time_file.write(time)

        # Start the scraping script
        try:
            subprocess.Popen(['python', 'main.py'])
            flash('Scraping script started successfully!')
        except Exception as e:
            flash(f'Error starting script: {e}')

        return redirect(url_for('index'))

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True, port=8000)

from rp_flask_personalwebsite import create_app

# Initialize the Flask application
app = create_app()

if __name__ == '__main__':

    # Run the bug locally in debug mode on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
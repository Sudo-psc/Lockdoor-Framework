from src.web_panel import app

if __name__ == '__main__':
    # Note: Port 5000 is often default. Ensure it's not conflicting if you have other services.
    # The host '0.0.0.0' makes it accessible from other devices on the same network.
    app.run(debug=True, host='0.0.0.0', port=5000)

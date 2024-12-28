from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import json
from werkzeug.middleware.proxy_fix import ProxyFix

class ServerConfig:
    CONFIG_FILE = "server_config.json"

    @staticmethod
    def load_config():
        try:
            with open(ServerConfig.CONFIG_FILE, 'r') as config_file:
                return json.load(config_file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON config: {str(e)}")

    @staticmethod
    def get(key):
        config = ServerConfig.load_config()
        return config.get(key)

class PDFSummarizerApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.configure_app()
        self.setup_routes()

    def configure_app(self):
        self.UPLOAD_FOLDER = ServerConfig.get('UPLOAD_FOLDER')
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        self.app.config['UPLOAD_FOLDER'] = self.UPLOAD_FOLDER

        # Apply ProxyFix for handling reverse proxies in production
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    def setup_routes(self):
        @self.app.route('/')
        def home():
            return send_from_directory('static', 'index.html')

        @self.app.route('/upload', methods=['POST'])
        def upload_file():
            if 'file' not in request.files:
                return jsonify({"error": "No file part in the request"}), 400

            file = request.files['file']

            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400

            if file:
                # Generate a unique filename to avoid conflicts
                unique_filename = f"{uuid.uuid4()}_{file.filename}"
                filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                return jsonify({"message": "File uploaded successfully", "filepath": filepath}), 200

    def run(self):
        # Disable debug mode and ensure host and port are set correctly for production
        self.app.run(
            debug=ServerConfig.get('DEBUG'), 
            host=ServerConfig.get('HOST'), 
            port=ServerConfig.get('PORT'), 
            threaded=True
        )

if __name__ == '__main__':
    app_instance = PDFSummarizerApp()
    app_instance.run()

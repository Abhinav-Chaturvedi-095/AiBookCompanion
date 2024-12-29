from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import json
from werkzeug.middleware.proxy_fix import ProxyFix
from utilities.utils import extract_text_from_pdf

class ServerConfig:
    CONFIG_FILE = "server_config.json"

    @staticmethod
    def load_config():
        try:
            with open(ServerConfig.CONFIG_FILE, 'r') as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            raise FileNotFoundError("server_config.json not found. Please create it.")
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

            if not file.filename.endswith('.pdf'):
                return jsonify({"error": "Only PDF files are allowed"}), 400

            try:
                unique_filename = f"{uuid.uuid4()}_{file.filename}"
                filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                return jsonify({"message": "File uploaded successfully", "filepath": filepath}), 200
            except Exception as e:
                return jsonify({"error": f"File upload failed: {str(e)}"}), 500

        @self.app.route('/summarize', methods=['POST'])
        def summarize():
            data = request.json
            if not data or 'filepath' not in data:
                return jsonify({"error": "No filepath provided"}), 400

            filepath = data['filepath']
            if not os.path.exists(filepath):
                return jsonify({"error": "File not found"}), 404

            try:
                text = extract_text_from_pdf(filepath)
                # summary = summarize_text(text)
                return jsonify({"summary": text}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy"}), 200

    def run(self):
        self.app.run(
            debug=ServerConfig.get('DEBUG'), 
            host=ServerConfig.get('HOST'), 
            port=ServerConfig.get('PORT'), 
            threaded=True
        )

if __name__ == '__main__':
    app_instance = PDFSummarizerApp()
    app_instance.run()

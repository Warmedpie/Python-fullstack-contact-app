from flask import Flask

from config import DevConfig
from src.data.database import init_db
from src.api.contact_routes import contact_bp
from src.api.email_routes import email_bp

def create_app(config_object=DevConfig):
    # static_url_path="" mounts Frontend/ at the root ("/") instead of the
    # Flask default of "/static" - Frontend/js/app.js is then served at
    # "/js/app.js", Frontend/css/style.css at "/css/style.css", etc.
    app = Flask(
        __name__,
        static_folder=config_object.FRONTEND_DIR,
        static_url_path="",
    )
    app.config.from_object(config_object)

    # Make sure the database file and tables exist before serving requests.
    init_db(app.config["DATABASE_PATH"])

    # Register API for contacts
    app.register_blueprint(contact_bp, url_prefix="/api")

    #Register API for emails
    app.register_blueprint(email_bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Flask's static handling serves any existing file under Frontend/,
    # but it won't serve index.html for "/" on its own - this fills that
    # one gap.
    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

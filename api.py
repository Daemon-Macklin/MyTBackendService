from flask import Flask
from flask_cors import CORS
from app import EXPORT_BLUEPRINTS
from flask_jwt_extended import JWTManager

# Create app
def createApp():
    app = Flask(__name__)
    app.config.from_pyfile('app/config.py')
    CORS(app, resources={r"/*": {"origins": "*"}})

    jwt = JWTManager(app)

    for bluePrint in EXPORT_BLUEPRINTS:
        app.register_blueprint(bluePrint)

    return app


app = createApp()

if __name__ == '__main__':
    app.run(host="0.0.0.0")

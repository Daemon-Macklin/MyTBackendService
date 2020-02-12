from flask import Flask
from app import EXPORT_BLUEPRINTS

# Create app
def createApp():
    app = Flask(__name__)
    app.config.from_pyfile('app/config.py')

    for bluePrint in EXPORT_BLUEPRINTS:
        app.register_blueprint(bluePrint)

    return app


app = createApp()

if __name__ == '__main__':
    app.run(host="0.0.0.0")

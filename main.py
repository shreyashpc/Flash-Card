import os
from flask import Flask
from flask import render_template
from flask_restful import Api
from application.apiEndpoints import CardAPI, DeckAPI, UserAPI
from application.database import db
from application.config import LocalDevelopmentConfig, ProductionConfig, StageConfig
from application import workers
from flask_cors import CORS
app = None
api = None
celery = None


def create_app():
    app = Flask(__name__, template_folder='templates')
    if os.getenv('ENV', "development") == "production":
        print('starting production server')
        app.config.from_object(ProductionConfig)
    elif os.getenv('ENV', "development") == "stage":
        app.logger.info("Staring stage.")
        print("Staring  stage")
        app.config.from_object(StageConfig)
        print("pushed config")
    else:
        print("Starting Local Development")
        app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)
    api = Api(app)
    app.app_context().push()

    # Create celery   
    celery = workers.celery

     # Update with configuration
    celery.conf.update(
        broker_url = app.config["CELERY_BROKER_URL"],
        result_backend = app.config["CELERY_RESULT_BACKEND"]
    )
    celery.Task = workers.ContextTask
    app.app_context().push()

    return app, api, celery



app, api, celery = create_app()

# enable CORS
CORS(app, supports_credentials=True)

from application.controller import *


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


api.add_resource(UserAPI, "/api/user/")
api.add_resource(DeckAPI, "/api/deck/", "/api/deck/<int:deck_id>")
api.add_resource(CardAPI, "/api/card/", "/api/card/<int:deck_id>", "/api/card/<int:card_id>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

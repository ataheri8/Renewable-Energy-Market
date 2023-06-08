from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from pm.config import PMConfig
from pm.modules.derinfo.models import *  # noqa
from pm.modules.enrollment.models import *  # noqa
from pm.modules.event_tracking.models import *  # noqa
from pm.modules.outbox.model import *  # noqa
from pm.modules.progmgmt.models import *  # noqa
from pm.modules.reports.models import *  # noqa
from pm.modules.serviceprovider.models import *  # noqa
from shared.smorest import api_factory
from shared.system import configuration, database, loggingsys


def create_app():
    app = Flask(__name__)
    CORS(app)
    api = api_factory(app=app, title="Program Management Core API", version="v1")
    load_dotenv()
    config = configuration.init_config(PMConfig)
    loggingsys.init(config)
    database.init(config)

    # Additional Flask configuration
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_HOL_CAL_FILE_SIZE
    app.url_map.strict_slashes = False

    # Load all routes + register blueprints
    from pm.restapi.derinfo.routes import derinfo
    from pm.restapi.enrollment.routes import contract, enrollment
    from pm.restapi.progmgmt.routes import program
    from pm.restapi.reports.routes import reports
    from pm.restapi.routes import system
    from pm.restapi.serviceprovider.routes import serviceprovider

    api.register_blueprint(system.blueprint)
    api.register_blueprint(program.blueprint)
    api.register_blueprint(serviceprovider.blueprint)
    api.register_blueprint(enrollment.blueprint)
    api.register_blueprint(contract.blueprint)
    api.register_blueprint(derinfo.blueprint)
    api.register_blueprint(reports.blueprint)

    return app


if __name__ == "__main__":
    app = create_app()

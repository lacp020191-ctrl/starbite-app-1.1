from flask import Flask, render_template
from flask_login import login_required
from models import db
from auth import auth, login_manager


app = Flask(__name__)
app.config.from_object("config.Config")

# Init DB
db.init_app(app)

# Init login manager
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Register Blueprint
app.register_blueprint(auth)


@app.route("/")
@login_required
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()

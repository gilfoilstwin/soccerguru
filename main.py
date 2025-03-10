from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import requests
from datetime import datetime
import json
import re

match = []

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CREATE TABLE
class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template("index.html", logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        email = request.form.get('email')
        result = db.session.execute(db.select(User).where(User.email == email))

        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            password=hash_and_salted_password,
            name=request.form.get('name'),
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("secrets"))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('secrets'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/secrets')
@login_required
def secrets():
    print(current_user.name)
    league_name = "PL"

    current_month_text = datetime.now().strftime('%B')
    current_day = datetime.now().strftime('%d')
    current_year_full = datetime.now().strftime('%Y')

    with open(f'stats/results_{league_name}.txt') as f:
        results = f.read().splitlines()

    with open(f'stats/teams_{league_name}.txt') as f:
        teams = f.read().splitlines()

    with open(f"stats/team_form_{league_name}.json") as file:
        form = json.load(file)

    sorted_form = dict(sorted(form.items()))

    return render_template("main_football_page.html", name=current_user.name, logged_in=True, all_posts=results,
                           all_teams=teams, form=sorted_form, current_month=current_month_text, current_day=current_day,
                           current_year=current_year_full, current_league="PL")


@app.route('/teams', methods=['POST'])
def show_team_scores():

    current_month_text = datetime.now().strftime('%B')
    current_day = datetime.now().strftime('%d')
    current_year_full = datetime.now().strftime('%Y')

    count = 0
    post_obj = []
    teams = []
    homeForm = {}
    awayForm = {}
    form = {}
    name = ""

    name = request.form["teamlist"]
    c_league = request.form.get("league_name")
    if c_league == "ELC":
        league_name = "ELC"
    else:
        league_name = "PL"

    print(f'League of gents is {league_name}')

    with open(f'stats/results_{league_name}.txt') as f:
        results = f.read().splitlines()

    with open(f'stats/teams_{league_name}.txt') as f:
        teams = f.read().splitlines()

    with open(f'stats/team_form_{league_name}.json') as file:
        form = json.load(file)

    for match in results:
        # if re.search(f"{name}\s+\d+\s+\:", match):
        if re.search(f"{name}", match):
            post_obj.append(match)
        else:
            print(f"{name} not found in {match}")

    teams.sort()
    sorted_form = dict(sorted(form.items()))

    return render_template("main_football_page.html", all_posts=post_obj, all_teams=teams, form=sorted_form, current_league=league_name, counter=count,
                           selectedTeam=name, current_month=current_month_text, current_day=current_day,
                           current_year=current_year_full)


@app.route('/championship', methods=["GET", "POST"])
def show_championship():
    league_name = "ELC"
    current_month_text = datetime.now().strftime('%B')
    current_day = datetime.now().strftime('%d')
    current_year_full = datetime.now().strftime('%Y')

    count = 0
    post_obj = []
    teams = []
    homeForm = {}
    awayForm = {}
    form = {}
    name = ""

    with open(f'stats/results_{league_name}.txt') as f:
        results = f.read().splitlines()

    with open(f'stats/teams_{league_name}.txt') as f:
        teams = f.read().splitlines()

    with open(f'stats/team_form_{league_name}.json') as file:
        form = json.load(file)

    teams.sort()
    sorted_form = dict(sorted(form.items()))

    return render_template("main_football_page.html", all_posts=post_obj, all_teams=teams, form=sorted_form, counter=count,
                           selectedTeam=name, current_month=current_month_text, current_day=current_day,current_league=league_name,
                           current_year=current_year_full)

@app.route('/premier_league', methods=["GET", "POST"])
def show_premiership():
    league_name = "PL"
    current_month_text = datetime.now().strftime('%B')
    current_day = datetime.now().strftime('%d')
    current_year_full = datetime.now().strftime('%Y')

    count = 0
    post_obj = []
    teams = []
    homeForm = {}
    awayForm = {}
    form = {}
    name = ""

    with open(f'stats/results_{league_name}.txt') as f:
        results = f.read().splitlines()

    with open(f'stats/teams_{league_name}.txt') as f:
        teams = f.read().splitlines()

    with open(f'stats/team_form_{league_name}.json') as file:
        form = json.load(file)

    teams.sort()
    sorted_form = dict(sorted(form.items()))

    return render_template("main_football_page.html", all_posts=post_obj, all_teams=teams, form=sorted_form, counter=count,
                           selectedTeam=name, current_month=current_month_text, current_day=current_day,current_league=league_name,
                           current_year=current_year_full)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/download')
@login_required
def download():
    # return send_from_directory('/static/files/', 'cheat_sheet.pdf')
    return send_from_directory('static', path="files/cheat_sheet.pdf")


if __name__ == "__main__":
    app.run(debug=True)

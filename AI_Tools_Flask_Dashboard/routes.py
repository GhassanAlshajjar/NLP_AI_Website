from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from firebase_admin import auth, db

routes = Blueprint('routes', __name__)

@routes.route("/")
def home():
    return render_template("dashboard.html", page_title="Home", breadcrumb=None)

@routes.route("/option<int:option_id>")
def option(option_id):
    # Define a mapping of option IDs to their titles
    option_titles = {
        1: "Document Analysis",
        2: "Text Summarizer",
        3: "Machine Learning Models",
        4: "Option 4",
        5: "Option 5",
        6: "AI Chatbot"
    }

    # Get the title for the current option ID
    page_title = option_titles.get(option_id, f"Option {option_id}")
    breadcrumb = f"Home / {page_title}"

    return render_template(
        "option.html",
        page_title=page_title,
        breadcrumb=breadcrumb
    )

@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check for missing fields
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html", page_title="Login")

        try:
            # Simulate Firebase login (password verification must be done client-side)
            user = auth.get_user_by_email(email)
            session['user_id'] = user.uid
            session['email'] = user.email
            user_ref = db.reference(f"users/{user.uid}")
            session['username'] = user_ref.get().get('username', 'Unknown')

            flash("Logged in successfully.", "success")
            return redirect(url_for("routes.home"))
        except auth.UserNotFoundError:
            flash("No account found with this email.", "danger")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("login.html", page_title="Login")


@routes.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Input validation
        if not username or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("signup.html", page_title="Sign Up")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html", page_title="Sign Up")

        try:
            # Create user in Firebase
            user = auth.create_user(email=email, password=password)
            # Save user data to Firebase Realtime Database
            ref = db.reference(f"users/{user.uid}")
            ref.set({
                "email": email,
                "username": username
            })
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("routes.login"))
        except auth.EmailAlreadyExistsError:
            flash("An account with this email already exists.", "danger")
        except Exception as e:
            flash(f"An error occurred during signup: {str(e)}", "danger")

    return render_template("signup.html", page_title="Sign Up")


@routes.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("routes.home"))


@routes.route("/profile", methods=["GET", "POST"])
def profile():
    if 'user_id' not in session:
        flash("You need to log in to access your profile.", "danger")
        return redirect(url_for("routes.login"))

    user_id = session['user_id']
    user_ref = db.reference(f"users/{user_id}")
    user_data = user_ref.get()

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email:
            flash("Username and email are required.", "danger")
            return render_template("profile.html", page_title="Profile", user_data=user_data)

        try:
            # Update email in Firebase Auth
            auth.update_user(user_id, email=email)
            # Update data in Firebase Realtime Database
            user_ref.update({"email": email, "username": username})
            session['email'] = email
            session['username'] = username

            if password:
                auth.update_user(user_id, password=password)

            flash("Profile updated successfully.", "success")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("profile.html", page_title="Profile", user_data=user_data)

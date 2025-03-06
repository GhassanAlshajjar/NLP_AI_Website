from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from firebase_admin import auth, db
from utils.document_analysis import compare_documents
from utils.web_plagiarism_checker import search_web_plagiarism
from utils.document_analysis_visualization import (
    generate_word_cloud_base64,
    generate_similarity_pie_chart_base64,
    generate_word_frequency_chart,
    generate_sentence_similarity_chart_base64
)
from utils.document_analysis import extract_text

routes = Blueprint('routes', __name__)

@routes.route("/")
def home():
    return render_template("dashboard.html", page_title="Home", breadcrumb=None)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}

def is_valid_file(file):
    return file and "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@routes.route("/document-analysis", methods=["GET", "POST"])
def document_analysis():
    print("🔍 [DEBUG] Entered document_analysis route")

    breadcrumb = "Home / Document Analysis"

    if request.args.get("reset"):
        return render_template("document_analysis.html", page_title="Document Analysis", breadcrumb=breadcrumb)

    similarity_score = 0
    online_results_doc1 = []
    online_results_doc2 = []
    plagiarism_percentage_doc1 = 0
    plagiarism_percentage_doc2 = 0
    most_matched_source_doc1 = None
    most_matched_source_doc2 = None
    doc1_info = None
    doc2_info = None
    wordcloud1 = None
    wordcloud2 = None
    similarity_chart = None
    word_freq_chart = None
    sentence_similarity_chart = None
    word_comparison = {}
    background_style = ""

    if request.method == "POST":
        print("🔍 [DEBUG] Detected POST request")

        doc1 = request.files.get("doc1")
        doc2 = request.files.get("doc2")

        if not doc1 and not doc2:
            print("❌ [DEBUG] No document uploaded")
            flash("Please upload at least one document.", "danger")
            return render_template("document_analysis.html", page_title="Document Analysis", breadcrumb=breadcrumb)

        total_size = request.content_length or 0
        if total_size > MAX_FILE_SIZE:
            print("❌ [DEBUG] File size too large")
            flash("Total file size exceeds the 5MB limit.", "danger")
            return render_template("document_analysis.html", page_title="Document Analysis", breadcrumb=breadcrumb)

        if doc1 and not is_valid_file(doc1):
            print(f"❌ [DEBUG] Invalid file type: {doc1.filename}")
            flash(f"Invalid file type for {doc1.filename}. Only .txt, .pdf, .docx allowed.", "danger")
            return render_template("document_analysis.html", page_title="Document Analysis", breadcrumb=breadcrumb)

        if doc2 and not is_valid_file(doc2):
            print(f"❌ [DEBUG] Invalid file type: {doc2.filename}")
            flash(f"Invalid file type for {doc2.filename}. Only .txt, .pdf, .docx allowed.", "danger")
            return render_template("document_analysis.html", page_title="Document Analysis", breadcrumb=breadcrumb)

        text1, text2 = "", ""

        if doc1:
            doc1.seek(0)
            text1 = extract_text(doc1)
            doc1.seek(0)
            word_count1 = len(text1.split())
            file_size1 = round(len(text1.encode('utf-8')) / 1024, 2)
            doc1_info = {"name": doc1.filename, "word_count": word_count1, "size": file_size1}
            print(f"✅ [DEBUG] Extracted text1: {len(text1.split())} words")

        if doc2:
            doc2.seek(0)
            text2 = extract_text(doc2)
            doc2.seek(0)
            word_count2 = len(text2.split())
            file_size2 = round(len(text2.encode('utf-8')) / 1024, 2)
            doc2_info = {"name": doc2.filename, "word_count": word_count2, "size": file_size2}
            print(f"✅ [DEBUG] Extracted text2: {len(text2.split())} words")

        if doc1 and doc2:
            print("🔍 [DEBUG] Running document similarity check")
            similarity_score, extracted_text1, extracted_text2, word_comparison = compare_documents(doc1, doc2)

            wordcloud1 = generate_word_cloud_base64(extracted_text1)
            wordcloud2 = generate_word_cloud_base64(extracted_text2)
            similarity_chart = generate_similarity_pie_chart_base64(similarity_score)
            word_freq_chart = generate_word_frequency_chart(extracted_text1, extracted_text2)
            sentence_similarity_chart = generate_sentence_similarity_chart_base64(extracted_text1, extracted_text2)

        if doc1:
            try:
                api_key = "AIzaSyAekjz6NytWtrJHsCeo5jJSlIwgDLjEFFM"
                cx = "90b789512521f489e"
                print("🔍 [DEBUG] Calling search_web_plagiarism for Document 1...")
                online_results_doc1 = search_web_plagiarism(text1, api_key, cx)
                print(f"🔍 [DEBUG] Online Results for Doc 1: {len(online_results_doc1)}")
            except Exception as e:
                print(f"❌ Plagiarism API Error (Doc 1): {str(e)}")

        if doc2:
            try:
                api_key = "AIzaSyAekjz6NytWtrJHsCeo5jJSlIwgDLjEFFM"
                cx = "90b789512521f489e"
                print("🔍 [DEBUG] Calling search_web_plagiarism for Document 2...")
                online_results_doc2 = search_web_plagiarism(text2, api_key, cx)
                print(f"🔍 [DEBUG] Online Results for Doc 2: {len(online_results_doc2)}")
            except Exception as e:
                print(f"❌ Plagiarism API Error (Doc 2): {str(e)}")

        if online_results_doc1:
            total_words_doc1 = len(text1.split())
            matched_words_doc1 = sum(len(result["snippet"].split()) for result in online_results_doc1)

            plagiarism_percentage_doc1 = round((matched_words_doc1 / total_words_doc1) * 100, 2) if total_words_doc1 else 0
            plagiarism_percentage_doc1 = min(plagiarism_percentage_doc1, 100)

            most_matched_source_doc1 = online_results_doc1[0]['link'] if online_results_doc1 else None
            print(f"✅ [DEBUG] Plagiarism Score (Doc 1): {plagiarism_percentage_doc1}%")

        if online_results_doc2:
            total_words_doc2 = len(text2.split())
            matched_words_doc2 = sum(len(result["snippet"].split()) for result in online_results_doc2)

            plagiarism_percentage_doc2 = round((matched_words_doc2 / total_words_doc2) * 100, 2) if total_words_doc2 else 0
            plagiarism_percentage_doc2 = min(plagiarism_percentage_doc2, 100)

            most_matched_source_doc2 = online_results_doc2[0]['link'] if online_results_doc2 else None
            print(f"✅ [DEBUG] Plagiarism Score (Doc 2): {plagiarism_percentage_doc2}%")

        background_style = "background-color: #DCDCDC; padding: 20px; border-radius: 10px;"

    return render_template(
        "document_analysis.html",
        page_title="Document Analysis",
        breadcrumb=breadcrumb, 
        similarity_score=similarity_score,
        online_results_doc1=online_results_doc1,
        online_results_doc2=online_results_doc2,
        plagiarism_percentage_doc1=plagiarism_percentage_doc1,
        plagiarism_percentage_doc2=plagiarism_percentage_doc2,
        most_matched_source_doc1=most_matched_source_doc1,
        most_matched_source_doc2=most_matched_source_doc2,
        doc1_info=doc1_info,
        doc2_info=doc2_info,
        wordcloud1=wordcloud1,
        wordcloud2=wordcloud2,
        similarity_chart=similarity_chart,
        word_freq_chart=word_freq_chart,
        sentence_similarity_chart=sentence_similarity_chart,
        word_comparison=word_comparison,
        background_style=background_style
    )

@routes.route("/option<int:option_id>")
def option(option_id):
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

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html", page_title="Login")

        try:
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

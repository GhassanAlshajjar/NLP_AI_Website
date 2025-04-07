from firebase_admin import auth
from flask import session
import uuid, tempfile
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from firebase_admin import auth, db
import cloudinary.uploader
import datetime
import re
import os
import nltk
import math
from AI_Tools_Flask_Dashboard.utils.document_analysis import compare_documents
from AI_Tools_Flask_Dashboard.utils.web_plagiarism_checker import search_web_plagiarism
from AI_Tools_Flask_Dashboard.utils.document_analysis_visualization import (
    generate_word_cloud_base64,
    generate_similarity_pie_chart_base64,
    generate_word_frequency_chart,
    generate_sentence_similarity_chart_base64
)
from AI_Tools_Flask_Dashboard.utils.document_analysis import extract_text
from AI_Tools_Flask_Dashboard.utils.plagiarism_checker import calculate_plagiarism_score
from AI_Tools_Flask_Dashboard.utils.metaphor_analysis import detect_metaphor_spans

routes = Blueprint('routes', __name__)

@routes.route("/")
def home():
    return render_template("dashboard.html", page_title="Home", breadcrumb=None)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DATASET_PATHS = [
    os.path.join(DATA_DIR, "MOH-X.csv"),
    os.path.join(DATA_DIR, "TroFi.csv"),
    os.path.join(DATA_DIR, "VUA_metaphor.csv")
]

# Ensure the model loads only once
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not os.environ.get("WERKZEUG_RUN_MAIN"):
    print("✅ Metaphor model (BERT) ready for inference.")


def is_valid_file(file):
    return file and "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@routes.route("/metaphor-detection", methods=["GET", "POST"])
def metaphor_detection():
    import uuid
    import tempfile
    import json

    breadcrumb = "Home / Metaphor Detection"
    text_content = ""
    detected_metaphors = []
    doc_info = {}
    stats = {}
    pagination = {}

    # Query parameters
    try:
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        per_page = 10

    page = int(request.args.get("page", 1))
    start_index = (page - 1) * per_page
    file_id = request.args.get("file_id")

    # Reset route
    if "reset" in request.args:
        return redirect(url_for("routes.metaphor_detection"))

    # Handle file upload
    if request.method == "POST":
        doc = request.files.get("document")
        if not doc:
            flash("Please upload a document.", "danger")
            return render_template("metaphor_detection.html", breadcrumb=breadcrumb)

        # Extract and save text
        text_content = extract_text(doc)
        words = re.findall(r'\b\w+\b', text_content)
        doc_info = {
            "name": doc.filename,
            "word_count": f"{len(words):,}",
            "size": f"{round(len(text_content.encode('utf-8')) / 1024, 2):,} KB"
        }

        # Save file to temp
        file_id = str(uuid.uuid4())
        temp_txt = os.path.join(tempfile.gettempdir(), f"{file_id}.txt")
        with open(temp_txt, "w", encoding="utf-8") as f:
            f.write(text_content)

        # Run metaphor detection once and save JSON
        all_metaphors, total_sentences = detect_metaphor_spans(text_content, start=0, per_page=10000)
        json_path = os.path.join(tempfile.gettempdir(), f"{file_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_metaphors, f, indent=2)

        return redirect(url_for("routes.metaphor_detection", file_id=file_id, page=1, per_page=per_page))

    # After file upload – handle pagination
    elif request.method == "GET" and file_id:
        temp_txt = os.path.join(tempfile.gettempdir(), f"{file_id}.txt")
        json_path = os.path.join(tempfile.gettempdir(), f"{file_id}.json")

        if not os.path.exists(temp_txt) or not os.path.exists(json_path):
            flash("Uploaded document not found or expired.", "danger")
            return redirect(url_for("routes.metaphor_detection"))

        # Load text and metaphors from cache
        with open(temp_txt, "r", encoding="utf-8") as f:
            text_content = f.read()

        with open(json_path, "r", encoding="utf-8") as f:
            all_metaphors = json.load(f)

        words = re.findall(r'\b\w+\b', text_content)
        doc_info = {
            "name": f"Uploaded File ({file_id[:8]})",
            "word_count": f"{len(words):,}",
            "size": f"{round(len(text_content.encode('utf-8')) / 1024, 2):,} KB"
        }

        total_sentences = len(nltk.sent_tokenize(text_content))
        total_metaphors = len(all_metaphors)
        detected_metaphors = all_metaphors[start_index:start_index + per_page]

        stats = {
            "total_sentences": total_sentences,
            "metaphors_detected": total_metaphors,
            "detection_rate": f"{round(100 * total_metaphors / max(1, total_sentences), 1)}%"
        }

        pagination = {
            "current_page": page,
            "per_page": per_page,
            "total": total_metaphors,
            "total_pages": math.ceil(total_metaphors / per_page),
            "file_id": file_id,
        }

        return render_template(
            "metaphor_detection.html",
            page_title="Metaphor Detection",
            breadcrumb=breadcrumb,
            text_content=text_content,
            detected_metaphors=detected_metaphors,
            doc_info=doc_info,
            stats=stats,
            pagination=pagination
        )

    return render_template("metaphor_detection.html", breadcrumb=breadcrumb)

@routes.route("/document-analysis", methods=["GET", "POST"])
def document_analysis():
    print("🔍 [DEBUG] Entered document_analysis route")

    breadcrumb = "Home / Document Analysis"

    if request.args.get("reset"):
        return render_template(
            "document_analysis.html",
            page_title="Document Analysis",
            breadcrumb=breadcrumb,
            word_comparison={},
            similarity_score=None,
            online_results_doc1=None,
            online_results_doc2=None,
            plagiarism_percentage_doc1=None,
            plagiarism_percentage_doc2=None,
            most_matched_source_doc1=None,
            most_matched_source_doc2=None,
            doc1_info=None,
            doc2_info=None,
            wordcloud1=None,
            wordcloud2=None,
            similarity_chart=None,
            word_freq_chart=None,
            sentence_similarity_chart=None,
            background_style=""
        )

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
                api_key = os.getenv("GOOGLE_API_KEY_DOC1")
                cx = os.getenv("GOOGLE_CX")
                print("🔍 [DEBUG] Calling search_web_plagiarism for Document 1...")
                online_results_doc1 = search_web_plagiarism(text1, api_key, cx)
                print(f"🔍 [DEBUG] Online Results for Doc 1: {len(online_results_doc1)}")
            except Exception as e:
                print(f"❌ Plagiarism API Error (Doc 1): {str(e)}")

        if doc2:
            try:
                api_key = os.getenv("GOOGLE_API_KEY_DOC2")
                cx = os.getenv("GOOGLE_CX")
                print("🔍 [DEBUG] Calling search_web_plagiarism for Document 2...")
                online_results_doc2 = search_web_plagiarism(text2, api_key, cx)
                print(f"🔍 [DEBUG] Online Results for Doc 2: {len(online_results_doc2)}")
            except Exception as e:
                print(f"❌ Plagiarism API Error (Doc 2): {str(e)}")

        if online_results_doc1:
            print(f"🔍 [DEBUG] Found {len(online_results_doc1)} sources for Doc 1")
            plagiarism_percentage_doc1 = calculate_plagiarism_score(text1, online_results_doc1)
            most_matched_source_doc1 = online_results_doc1[0]['link'] if online_results_doc1 else None
            print(f"✅ [DEBUG] Improved Plagiarism Score (Doc 1): {plagiarism_percentage_doc1}%")
        else:
            print("⚠️ [DEBUG] No plagiarism results found for Doc 1")

        if online_results_doc2:
            print(f"🔍 [DEBUG] Found {len(online_results_doc2)} sources for Doc 2")
            plagiarism_percentage_doc2 = calculate_plagiarism_score(text2, online_results_doc2)
            most_matched_source_doc2 = online_results_doc2[0]['link'] if online_results_doc2 else None
            print(f"✅ [DEBUG] Improved Plagiarism Score (Doc 2): {plagiarism_percentage_doc2}%")
        else:
            print("⚠️ [DEBUG] No plagiarism results found for Doc 2")

        
        # if "user_id" not in session:
        #     flash("You need to log in to upload files.", "danger")
        #     return redirect(url_for("routes.login"))

        # user_id = session["user_id"]  # Get current user ID

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
        word_comparison=word_comparison or {},
        background_style=background_style
    )

@routes.route("/option<int:option_id>")
def option(option_id):
    option_titles = {
        1: "Document Analysis",
        2: "Text Summarizer",
        3: "Machine Learning Models",
        4: "Metaphor Detection",
        5: "Option 5",
        6: "AI Chatbot"
    }

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
            user_ref = db.reference(f"users/{user.uid}")
            user_data = user_ref.get()

            session['user_id'] = user.uid
            session['email'] = user.email
            session['username'] = user_data.get('username', 'Unknown')
            session.permanent = True

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

        if not username or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("signup.html", page_title="Sign Up")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html", page_title="Sign Up")

        try:
            user = auth.create_user(email=email, password=password)
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
    session.pop('user_id', None)
    session.pop('email', None)
    session.pop('username', None)
    session.permanent = False
    flash("Logged out successfully.", "success")
    return redirect(url_for("routes.home"))

@routes.route("/profile", methods=["GET", "POST"])
def profile():
    if 'user_id' not in session:
        flash("You need to log in to access your profile.", "danger")
        return redirect(url_for("routes.login"))

    user_id = session['user_id']
    user_ref = db.reference(f"users/{user_id}")
    user_data = user_ref.get() or {}

    if request.method == "POST":
        username = request.form.get("username", user_data.get("username", ""))
        email = request.form.get("email", user_data.get("email", ""))

        try:
            # Update only changed fields, preserving existing data
            user_update_data = {
                "email": email,
                "username": username,
            }
            user_ref.update(user_update_data)

            # Also update session variables
            session['email'] = email
            session['username'] = username

            flash("Profile updated successfully.", "success")

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("profile.html", page_title="Profile", user_data=user_data)




from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)


# -----------------------------------------
# Skill Categories
# -----------------------------------------

SKILL_CATEGORIES = {
    "Backend": [
        "python", "flask", "django", "java",
        "spring boot", "node.js", "sql"
    ],
    "Frontend": [
        "html", "css", "javascript", "react", "angular"
    ],
    "AI/ML": [
        "machine learning", "deep learning", "ai",
        "tensorflow", "pytorch"
    ],
    "UI/UX": [
        "ui/ux", "figma", "canva", "design"
    ],
    "Testing": [
        "testing", "selenium", "qa"
    ],
    "Data Science": [
        "data science", "pandas", "numpy", "data analysis"
    ],
    "Documentation": [
        "documentation", "research", "powerpoint"
    ]
}


# -----------------------------------------
# Create Database
# -----------------------------------------

def create_database():

    connection = sqlite3.connect("database.db")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            skills TEXT NOT NULL,
            experience TEXT NOT NULL,
            role TEXT NOT NULL,
            interests TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# -----------------------------------------
# Get Skill Categories
# -----------------------------------------

def get_categories(skills):

    categories = set()

    for skill in skills:

        for category, category_skills in SKILL_CATEGORIES.items():

            if skill in category_skills:
                categories.add(category)

    return categories


# -----------------------------------------
# Home
# -----------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -----------------------------------------
# Profile
# -----------------------------------------

@app.route("/profile")
def profile():

    return render_template("profile.html")


# -----------------------------------------
# Save Profile
# -----------------------------------------

@app.route("/save_profile", methods=["POST"])
def save_profile():

    name = request.form["name"]
    email = request.form["email"]
    skills = request.form["skills"]
    experience = request.form["experience"]
    role = request.form["role"]
    interests = request.form["interests"]

    connection = sqlite3.connect("database.db")

    connection.execute("""
        INSERT INTO users
        (name, email, skills, experience, role, interests)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        skills,
        experience,
        role,
        interests
    ))

    connection.commit()
    connection.close()

    return render_template("success.html")


# -----------------------------------------
# Match
# -----------------------------------------

@app.route("/match", methods=["GET", "POST"])
def match():

    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row

    users = connection.execute(
        "SELECT * FROM users"
    ).fetchall()

    results = []
    selected_user = None

    if request.method == "POST":

        user_id = request.form["user_id"]

        selected_user = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        # Selected user's skills
        selected_skills = set(
            skill.strip().lower()
            for skill in selected_user["skills"].split(",")
        )

        selected_categories = get_categories(
            selected_skills
        )

        # Selected user's interests
        selected_interests = set(
            interest.strip().lower()
            for interest in selected_user["interests"].split(",")
        )

        candidates = []

        for user in users:

            if user["id"] == selected_user["id"]:
                continue

            other_skills = set(
                skill.strip().lower()
                for skill in user["skills"].split(",")
            )

            other_categories = get_categories(
                other_skills
            )

            other_interests = set(
                interest.strip().lower()
                for interest in user["interests"].split(",")
            )

            candidates.append({
                "user": user,
                "skills": other_skills,
                "categories": other_categories,
                "interests": other_interests
            })

        # -----------------------------------------
        # Build Diverse Team
        # -----------------------------------------

        covered_categories = set(selected_categories)
        covered_skills = set(selected_skills)

        selected_teammates = []

        for _ in range(4):

            if not candidates:
                break

            best_candidate = None
            best_score = -1

            best_new_categories = set()
            best_new_skills = set()

            for candidate in candidates:

                user = candidate["user"]

                candidate_categories = candidate["categories"]
                candidate_skills = candidate["skills"]
                candidate_interests = candidate["interests"]

                # New categories
                new_categories = (
                    candidate_categories -
                    covered_categories
                )

                # New skills
                new_skills = (
                    candidate_skills -
                    covered_skills
                )

                # -----------------------------------------
                # Skill Score
                # -----------------------------------------

                category_score = (
                    len(new_categories) * 10
                )

                skill_score = (
                    len(new_skills) * 2
                )

                # -----------------------------------------
                # Experience Score
                # -----------------------------------------

                experience_score = 0

                if user["experience"] == selected_user["experience"]:

                    experience_score = 5

                else:

                    experience_score = 3

                # -----------------------------------------
                # Role Diversity Score
                # -----------------------------------------

                role_score = 0

                if user["role"] != selected_user["role"]:

                    role_score = 8

                # -----------------------------------------
                # Interest Score
                # -----------------------------------------

                common_interests = (
                    selected_interests &
                    candidate_interests
                )

                interest_score = (
                    len(common_interests) * 3
                )

                # -----------------------------------------
                # Total Score
                # -----------------------------------------

                total_score = (
                    category_score +
                    skill_score +
                    experience_score +
                    role_score +
                    interest_score
                )

                if total_score > best_score:

                    best_score = total_score

                    best_candidate = candidate

                    best_new_categories = (
                        new_categories
                    )

                    best_new_skills = (
                        new_skills
                    )

            # -----------------------------------------
            # No Candidate
            # -----------------------------------------

            if best_candidate is None:
                break

            user = best_candidate["user"]

            candidate_categories = (
                best_candidate["categories"]
            )

            # -----------------------------------------
            # Match Percentage
            # -----------------------------------------

            if len(candidate_categories) > 0:

                match_percentage = (
                    len(best_new_categories)
                    /
                    len(candidate_categories)
                ) * 100

            else:

                match_percentage = 0

            match_percentage = min(
                match_percentage,
                100
            )

            # -----------------------------------------
            # Common Interests
            # -----------------------------------------

            common_interests = (
                selected_interests &
                best_candidate["interests"]
            )

            selected_teammates.append({

                "name": user["name"],

                "email": user["email"],

                "skills": user["skills"],

                "role": user["role"],

                "experience": user["experience"],

                "match": round(
                    match_percentage,
                    2
                ),

                "different": ", ".join(
                    best_new_skills
                ),

                "categories": ", ".join(
                    best_new_categories
                ),

                "interests": ", ".join(
                    common_interests
                ),

                "status": "team"

            })

            # -----------------------------------------
            # Update Team Skills
            # -----------------------------------------

            covered_categories.update(
                candidate_categories
            )

            covered_skills.update(
                best_candidate["skills"]
            )

            candidates.remove(
                best_candidate
            )

        # -----------------------------------------
        # Not Matched
        # -----------------------------------------

        not_matched = []

        for candidate in candidates:

            user = candidate["user"]

            not_matched.append({

                "name": user["name"],

                "email": user["email"],

                "skills": user["skills"],

                "role": user["role"],

                "experience": user["experience"],

                "match": 0,

                "different": "",

                "categories": "",

                "interests": "",

                "status": "not_matched"

            })

        # -----------------------------------------
        # Final Results
        # -----------------------------------------

        results = (
            selected_teammates +
            not_matched
        )

    connection.close()

    return render_template(
        "match.html",

        users=users,

        results=results,

        selected_user=selected_user,

        team_results=(
            results[:4]
            if selected_user
            else []
        ),

        not_matched_results=(
            results[4:]
            if selected_user
            else []
        )
    )


# -----------------------------------------
# Run Application
# -----------------------------------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)
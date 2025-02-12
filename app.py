import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_url_path='/assets', static_folder='assets')

# Set the secret key
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

DATA_FILE = "users.json"

# Ensure the data file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# Helper function to read users from the JSON file
def read_users():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Helper function to write users to the JSON file
def write_users(users):
    with open(DATA_FILE, "w") as file:
        json.dump(users, file, indent=4)

# Enum for User Types
USER_TYPE = ['admin', 'user']

# Seed Admin User
def seed_admin():
    users = read_users()
    admin_email = 'admin@example.com'
    if not any(user.get('email') == admin_email for user in users):
        admin_user = {
            'id': 1,
            'name': 'Admin User',
            'email': admin_email,
            'password': generate_password_hash('adminpassword'),
            'image': 'default.png',
            'type': 'admin'
        }
        users.append(admin_user)
        write_users(users)
        print("Admin user added.")
    else:
        print("Admin user already exists.")

seed_admin()

# Serve uploaded files
@app.route('/assets/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('assets/uploads', filename)

@app.route("/", methods=["GET", "POST"])
def login():
    message = None  # Initialize a variable for message
    message_type = None  # Initialize a variable for message type

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        users = read_users()
        user = next((u for u in users if 'email' in u and u['email'] == email), None)
        
        if user and check_password_hash(user['password'], password):
            if user['type'] == 'admin':
                return redirect(url_for("dashboard"))
            elif user['type'] == 'user':
                message = "Hi, welcome!"  # Set the success message
                message_type = "success"  # Set the message type (success)
                return redirect(url_for("login", message=message, message_type=message_type))
        else:
            message = "Invalid email or password"  # Set the error message
            message_type = "danger"  # Set the message type (error)

    return render_template("login.html", message=message, message_type=message_type)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/users")
def users():
    users = read_users()
    return render_template("users.html", users=users)

@app.route("/add_user", methods=["POST"])
def add_user():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    image = request.files.get("image")
    user_type = request.form.get("type")
    if not name or not email or not password or not image or user_type not in USER_TYPE:
        flash("All fields are required and type must be either 'admin' or 'user'", "danger")
        return redirect(url_for("users"))
    image_path = os.path.join("assets/uploads", image.filename)
    os.makedirs("assets/uploads", exist_ok=True)
    image.save(image_path)
    users = read_users()
    users.append({
        "id": len(users) + 1,
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "image": image.filename,
        "type": user_type
    })
    write_users(users)
    flash("User added successfully", "success")
    return redirect(url_for("users"))

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    users = read_users()
    users = [user for user in users if user["id"] != user_id]
    write_users(users)
    flash("User deleted successfully", "success")
    return redirect(url_for("users"))

@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        image = request.files.get("image")

        # Ensure required fields are provided
        if not name or not email:
            flash("Name and email are required", "danger")
            return redirect(url_for("users"))

        # Fetch users and locate the one to edit
        users = read_users()
        user = next((user for user in users if user["id"] == user_id), None)
        if not user:
            flash("User not found", "danger")
            return redirect(url_for("users"))

        # Update user details
        user['name'] = name
        user['email'] = email

        # Handle image upload if provided
        if image:
            image_path = os.path.join("assets/uploads", image.filename)
            os.makedirs("assets/uploads", exist_ok=True)
            image.save(image_path)
            user['image'] = image.filename

        # Save updated user data
        write_users(users)
        flash("User updated successfully", "success")
        return redirect(url_for("users"))

    # For GET request, fetch user details
    users = read_users()
    user = next((user for user in users if user["id"] == user_id), None)
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("users"))

    return render_template("edit_user.html", user=user)


if __name__ == "__main__":
    app.run(debug=True, port=8000)

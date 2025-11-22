# from custom.models import *
from custom.authentication import *
from custom.functions import *
from custom.models import *
from custom.import_modules import *

generated_key = generate_secret_key()
#print(generated_key)

app = Flask(__name__)
# Use secret key from environment or generated key
app.secret_key = os.getenv('SECRET_KEY', generated_key)
csrf = CSRFProtect(app)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# MongoDB is configured in mongodb_config.py and imported via import_modules
# No additional configuration needed here


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == a_email and password == a_pass:
            session["logged_in"] = True
            session["is_admin"] = True
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))

        user = mongodb_models.find_user_by_email(email)

        if user:
            stored_password = user['password']
            if check_password_hash(stored_password, password):
                session["logged_in"] = True
                session["user_id"] = str(user['_id'])
                session["user_name"] = user['name']
                session["profession"] = user['profession']
                flash("Login successful!", "success")
                return redirect(url_for("home"))
            else:
                flash("Invalid email or password. Please try again.", "danger")
        else:
            flash("User Not Found!. Please try again.", "danger")

    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        age = request.form.get("age")
        gender = request.form.get("gender")
        profession = request.form.get("profession")

        print(full_name, email, password, age, gender, profession)

        if not full_name or not email or not password or not age:
            flash("All fields are required!", "danger")
            return render_template(
                "pages/signup.html",
                name=full_name,
                email=email,
                age=age,
                gender=gender,
                profession=profession,
            )

        existing_user = mongodb_models.find_user_by_email(email)

        if existing_user:
            flash("Email already exists. Please use a different one.", "danger")
            return render_template(
                "pages/signup.html",
                name=full_name,
                email=email,
                age=age,
                gender=gender,
                profession=profession,
            )

        hashed_password = generate_password_hash(password)

        user_id = mongodb_models.create_user(
            full_name, email, hashed_password, age, gender, profession
        )
        
        if not user_id:
            flash("Registration failed. Please try again.", "danger")
            return render_template(
                "pages/signup.html",
                name=full_name,
                email=email,
                age=age,
                gender=gender,
                profession=profession,
            )

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("index"))

    return render_template("pages/signup.html")


@app.route("/about")
def about():
    return render_template("pages/about.html")


@app.route('/calculateIndex', methods=['GET', 'POST'])
def calculateIndex():
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("index"))
    
    if request.method == 'POST':
        if 'imageUpload' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        files = request.files.getlist('imageUpload')
        if len(files) == 0:
            flash('No files uploaded', 'danger')
            return redirect(request.url)

        total_decayed = 0
        total_missing = 0
        total_filled = 0
        total_index = 0

        results_list = []
        files = files[:5]

        for file in files:
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                image = Image.open(filepath)

                # YOLOv10 predictions
                yolo_predictions_v10 = yolo_model_v10.predict(filepath, conf=confidence_threshold_yolo)
                yolo_boxes_v10 = torch.tensor(yolo_predictions_v10[0].boxes.xyxy.cpu().numpy()).to(device)
                yolo_scores_v10 = torch.tensor(yolo_predictions_v10[0].boxes.conf.cpu().numpy()).to(device)
                yolo_labels_v10 = torch.tensor(yolo_predictions_v10[0].boxes.cls.cpu().numpy().astype(int)).to(device)

                # YOLOv11 predictions
                yolo_predictions_v11 = yolo_model_v11.predict(filepath, conf=confidence_threshold_yolo)
                yolo_boxes_v11 = torch.tensor(yolo_predictions_v11[0].boxes.xyxy.cpu().numpy()).to(device)
                yolo_scores_v11 = torch.tensor(yolo_predictions_v11[0].boxes.conf.cpu().numpy()).to(device)
                yolo_labels_v11 = torch.tensor(yolo_predictions_v11[0].boxes.cls.cpu().numpy().astype(int)).to(device)

                # Combine YOLO predictions
                all_boxes = torch.cat([yolo_boxes_v10, yolo_boxes_v11])
                all_scores = torch.cat([yolo_scores_v10, yolo_scores_v11])
                all_labels = torch.cat([yolo_labels_v10, yolo_labels_v11])

                all_boxes, all_labels, all_scores = filter_valid_labels(all_boxes, all_labels, all_scores)

                if all_boxes.size(0) == 0:
                    flash(f"No valid boxes found for {filename}. Skipping.", "warning")
                    continue

                cluster_labels = cluster_boxes_with_dbscan(all_boxes, eps=0.8, min_samples=1)

                final_boxes = []
                final_scores = []
                final_labels = []

                image_decayed_count = 0
                image_missing_count = 0
                image_filled_count = 0

                for cluster_label in set(cluster_labels):
                    cluster_indices = np.where(cluster_labels == cluster_label)[0]

                    cluster_boxes = all_boxes[cluster_indices]
                    cluster_scores = all_scores[cluster_indices]
                    cluster_labels_in_cluster = all_labels[cluster_indices]

                    avg_box = cluster_boxes.mean(dim=0)
                    avg_score = cluster_scores.mean()
                    final_label = torch.mode(cluster_labels_in_cluster).values.item()

                    final_boxes.append(avg_box)
                    final_scores.append(avg_score)
                    final_labels.append(final_label)

                    if final_label == 0:
                        image_decayed_count += 1
                    elif final_label == 1: 
                        image_missing_count += 1
                    elif final_label == 2: 
                        image_filled_count += 1

                if len(final_boxes) > 0:
                    final_boxes = torch.stack(final_boxes)
                    final_scores = torch.tensor(final_scores).to(device)
                    final_labels = torch.tensor(final_labels).to(device)

                    output_path = os.path.join(app.config['OUTPUT_FOLDER'], f'yolo_combined_{filename}')
                    visualize_predictions(image, final_boxes.cpu().numpy(), final_labels.cpu().numpy(),
                                          final_scores.cpu().numpy(), output_path)

                    total_decayed += image_decayed_count
                    total_missing += image_missing_count
                    total_filled += image_filled_count

                    image_total_index = image_decayed_count + image_missing_count + image_filled_count
                    total_index += image_total_index

                    results_list.append({
                        'image': f'yolo_combined_{filename}',
                        'annotated_image': output_path,
                        'boxes': final_boxes.cpu().numpy().tolist(),
                        'scores': final_scores.cpu().numpy().tolist(),
                        'labels': final_labels.cpu().numpy().tolist(),
                        'decayed_count': image_decayed_count,
                        'missing_count': image_missing_count,
                        'filled_count': image_filled_count,
                        'total_index': image_total_index
                    })

        session['results_list'] = results_list
        session['total_decayed'] = total_decayed
        session['total_missing'] = total_missing
        session['total_filled'] = total_filled
        session['total_index'] = total_index
        
        session['combined_results'] = {
            'total_combined_decayed': total_decayed,
            'total_combined_missing': total_missing,
            'total_combined_filled': total_filled,
            'total_combined_index': total_index
        }
        session.modified = True 
        
        #print(f"Session Combined Results (Inside calculateIndex): {session['combined_results']}")

        return jsonify({'redirect': url_for('showResults')})

    return render_template('pages/calculateIndex.html')




@app.route('/showResults')
def showResults():
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("index"))

    results_list = session.get('results_list', [])
    combined_results = session.get('combined_results', {})
    
    print(f"Combined Results: {combined_results}")
    print(f"Total Combined Index: {combined_results.get('total_combined_index')}")

    user_profession = session.get('profession', 'patient')

    return render_template(
        'pages/show_results.html', 
        results=results_list, 
        combined_results=combined_results, 
        profession=user_profession
    )


@app.route("/save")
def save():
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("index"))
    
    combined_results = session.get('combined_results', {})
    
    return render_template('pages/save.html', combined_results=combined_results)

@app.route("/save_patient", methods=["POST"])
def save_patient():
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("index"))

    try:
        patient_name = request.form.get("patient_name")
        dmft_index = session['combined_results']['total_combined_index']
        decayed_tooth = session['combined_results']['total_combined_decayed']
        missing_tooth = session['combined_results']['total_combined_missing']
        filled_tooth = session['combined_results']['total_combined_filled']
        doctor_id = session.get("user_id")

        result_id = mongodb_models.create_result(
            doctor_id, patient_name, dmft_index, decayed_tooth, missing_tooth, filled_tooth
        )
        
        if not result_id:
            flash("Failed to save patient data. Please try again.", "danger")
            return redirect(url_for("save"))

        flash("Patient data saved successfully!", "success")
        return redirect(url_for("home"))

    except Exception as e:
        flash(f"An error occurred while saving patient data: {e}", "danger")
        return redirect(url_for("save"))
    

@app.route("/patients_data", methods=["GET", "POST"])
def patients_data():
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("index"))
    
    doctor_id = session.get('user_id')

    patients_results = mongodb_models.get_results_by_doctor(doctor_id)
    
    # Convert MongoDB results to format expected by template
    formatted_results = []
    for result in patients_results:
        formatted_results.append((
            str(result['_id']),  # patient_id (using result _id)
            result['patient_name'],
            result['dmft_index'],
            result['decayed_tooth'],
            result['missing_tooth'],
            result['filled_tooth']
        ))
    patients_results = formatted_results

    return render_template('pages/patients_data.html', users=patients_results)


@app.route("/delete_patient/<string:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("index"))

    doctor_id = session.get('user_id')

    try:
       
        success = mongodb_models.delete_result(patient_id, doctor_id)
        if not success:
            flash("Error deleting patient data: Result not found or access denied.", "danger")
            return redirect(url_for("patients_data"))

        flash("Patient data deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting patient data: {e}", "danger")

    return redirect(url_for("patients_data"))



# @app.route('/results_relevent')
# def results_relevent():
#     return render_template("pages/results_relevent.html")


@app.route("/contact")
def contact():
    return render_template("pages/contact.html")


@app.route("/instructions")
def instructions():
    return render_template("pages/instructions.html")


@app.route("/admin_results_info")
def admin_results_info():
    if not session.get("logged_in") or not session.get("is_admin"):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for("index"))

    results = mongodb_models.get_all_results()
    doctors = mongodb_models.get_users_by_profession('doctor')

    doctor_dict = {str(doctor['_id']): doctor['name'] for doctor in doctors}

    updated_results = []
    for result in results:
        doctor_id = str(result['doctor_id'])
        doctor_name = doctor_dict.get(doctor_id, "Unknown Doctor")
        updated_results.append((
            str(result['_id']),  # patient_id (using result _id)
            doctor_name,
            result['patient_name'],
            result['dmft_index'],
            result['decayed_tooth'],
            result['missing_tooth'],
            result['filled_tooth']
        ))

    return render_template("admin/admin_results_info.html", users=updated_results)


@app.route("/admin_patient_info")
def admin_patient_info():
    if not session.get("logged_in") or not session.get("is_admin"):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for("index"))
     
    users = mongodb_models.get_users_by_profession('patient')
    
    # Convert MongoDB results to format expected by template
    formatted_users = []
    for user in users:
        formatted_users.append((
            str(user['_id']),  # user_id
            user['name'],
            user['email'],
            user['password'],
            user['age'],
            user['gender'],
            user['profession']
        ))
    users = formatted_users
    print(users)

    return render_template("admin/admin_patient_info.html", users = users)

@app.route("/admin_doctor_info")
def admin_doctor_info():
    if not session.get("logged_in") or not session.get("is_admin"):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for("index"))

    users = mongodb_models.get_users_by_profession('doctor')
    
    # Convert MongoDB results to format expected by template
    formatted_users = []
    for user in users:
        formatted_users.append((
            str(user['_id']),  # user_id
            user['name'],
            user['email'],
            user['password'],
            user['age'],
            user['gender'],
            user['profession']
        ))
    users = formatted_users
    print(users)

    return render_template("admin/admin_doctor_info.html", users=users)

@app.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("logged_in") or not session.get("is_admin"):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for("index"))
    return render_template("admin/admin_dashboard.html")


@app.route("/delete_user/<string:user_id>", methods=["POST"])
def delete_user(user_id):
    if not session.get("logged_in") or not session.get("is_admin"):
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for("index"))
    
    admin_page = 0
    if request.method == "POST":
        admin_page = request.form.get("admin_doctor_info")

    try:
        admin_page = int(admin_page)
    except ValueError:
        admin_page = 0
        

    try:
        success = mongodb_models.delete_user(user_id)
        if admin_page == 1:
            # Also delete all results for this doctor
            mongodb_models.delete_results_by_doctor(user_id)
        
        if not success:
            flash("Error deleting user: User not found.", "danger")
            if admin_page==1:
                return redirect(url_for("admin_doctor_info"))
            elif admin_page==2:
                return redirect(url_for("admin_patient_info"))
            elif admin_page == 3:
                return redirect(url_for("admin_results_info"))
            return redirect(url_for("admin_dashboard"))
        flash("User deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting user: {e}", "danger")

    if admin_page==1:
        return redirect(url_for("admin_doctor_info"))
    elif admin_page==2:
        return redirect(url_for("admin_patient_info"))
    elif admin_page == 3:
        return redirect(url_for("admin_results_info"))
    return redirect(url_for("admin_dashboard"))


@app.route("/editProfile/<string:user_id>", methods=["GET", "POST"])
def editProfile(user_id):
    if not session.get("logged_in"):
        flash("Access denied. Login First.", "danger")
        return redirect(url_for("index"))

    # MongoDB operations don't need cursor management

    admin_page = request.args.get("admin_doctor_info", "0")
    # print(f"Initial GET admin_page: {admin_page}")

    try:
        admin_page = int(admin_page) 
    except ValueError:
        admin_page = 0  

    
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        age = request.form.get("age")
        gender = request.form.get("gender")
        profession = request.form.get("profession")
        admin_id = request.form.get("adminID")
        admin_page = request.form.get("admin_doctor_info", "0") 
        # print(f"POST admin_page before conversion: {admin_page}")

        try:
            admin_page = int(admin_page)
        except ValueError:
            admin_page = 0

        # print(f"POST admin_page after conversion: {admin_page}")
        

        hardcoded_admin_id = "48a669b7a54d3b0dea3197741aa6d2699774446a7cd82e0d"

        if not name or not email or not age or not gender or not profession:
            flash("All fields except password are required!", "danger")
            return redirect(url_for("editProfile", user_id=user_id))

        update_data = {
            "name": name,
            "email": email,
            "age": age,
            "gender": gender,
            "profession": profession
        }
        
        if password:
            hashed_password = generate_password_hash(password)
            update_data["password"] = hashed_password
        
        success = mongodb_models.update_user(user_id, update_data)
        
        if not success:
            flash("Error updating user: User not found.", "danger")
            return redirect(url_for("editProfile", user_id=user_id))

        flash("User updated successfully!", "success")
        # print(f"admin_id: {admin_id}")
        # print(f"hardcoded_admin_id: {hardcoded_admin_id}")
        # print(f"admin_page: {admin_page}")

        if admin_page == 1:
            return redirect(url_for("admin_doctor_info"))
        elif admin_page == 2:
            return redirect(url_for("admin_patient_info"))
        else:
            return redirect(url_for("home"))
    else:
        user = mongodb_models.find_user_by_id(user_id)

        if user:
            admin_id = request.args.get("adminID", "")
            return render_template(
                "pages/editProfile.html",
                user_id=user_id,
                name=user['name'],
                email=user['email'],
                age=user['age'],
                gender=user['gender'],
                profession=user['profession'],
                admin_id=admin_id,
                admin_page=admin_page
            )
        else:
            flash("User not found!", "danger")
            return redirect(url_for("home"))


@app.route('/suggestions', methods=['POST'])
def suggestions():
    dmft_index = int(request.form.get('dmft_index', 0))

    return render_template('pages/suggestions.html', dmft_index=dmft_index)


@app.route("/home")
def home():
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "danger")
        return redirect(url_for("index"))
    user_profession = session.get('profession', 'patient')
    return render_template("pages/home.html", user_name=session.get("user_name"), profession=user_profession)


@app.route("/logout")
def logout():
    upload_folder = os.path.join(os.getcwd(), 'static', 'uploads')
    output_folder = os.path.join(upload_folder, 'output')

    file_types = ['*.jpg', '*.jpeg', '*.png']
    for file_type in file_types:
        for file_path in glob.glob(os.path.join(upload_folder, file_type)):
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")  
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

    # Remove image files from the output folder
    for file_type in file_types:
        for file_path in glob.glob(os.path.join(output_folder, file_type)):
            try:
                os.remove(file_path)
                #print(f"Deleted file: {file_path}") 
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    # For production deployment, debug should be False
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
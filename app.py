import os
import json
import re
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db, seed_sample_data
from ai_engine import analyze_project, chat_reply

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'project-after-life-super-secret-key-2026')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Context processor for global template variables
@app.context_processor
def inject_global_data():
    current_user = None
    unread_notifications_count = 0
    notifications = []
    
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        current_user = cursor.fetchone()
        
        cursor.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (session['user_id'],)
        )
        notifications = cursor.fetchall()
        
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0",
            (session['user_id'],)
        )
        row = cursor.fetchone()
        unread_notifications_count = row['cnt'] if row else 0
        conn.close()
        
    return {
        'current_user': current_user,
        'unread_notifications_count': unread_notifications_count,
        'notifications_dropdown': notifications,
        'current_year': datetime.now().year
    }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "info")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please sign in to access this page.", "info")
                return redirect(url_for('login'))
            if session.get('role') != role and session.get('role') != 'admin':
                flash(f"This page requires {role.capitalize()} access.", "warning")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Home & Auth Routes ---

@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()
    
    # Query summary metrics
    cursor.execute("SELECT COUNT(*) as cnt FROM projects WHERE submission_status = 'Published'")
    total_published = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT SUM(approved_amount) as total FROM project_interests WHERE status = 'Funding Approved'")
    row = cursor.fetchone()
    total_funded_val = row['total'] if row and row['total'] else 0
    
    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'company'")
    total_companies = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM projects WHERE development_stage != 'Planning' AND funding_status = 'Funding Approved'")
    active_devs = cursor.fetchone()['cnt']
    
    # Featured Projects for Showcase
    cursor.execute("""
        SELECT p.*, u.organization as student_college
        FROM projects p
        JOIN users u ON p.student_id = u.id
        WHERE p.submission_status = 'Published'
        ORDER BY p.created_at DESC LIMIT 3
    """)
    featured_projects = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', 
                           total_published=total_published, 
                           total_funded_val=total_funded_val,
                           total_companies=total_companies,
                           active_devs=active_devs,
                           featured_projects=featured_projects)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            session['email'] = user['email']
            flash(f"Welcome back, {user['name']}!", "success")
            
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'company':
                return redirect(url_for('company_explorer'))
            else:
                return redirect(url_for('index'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')
        organization = request.form.get('organization', '').strip()
        department = request.form.get('department', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        bio = request.form.get('bio', '').strip()
        
        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template('register.html')
            
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash("An account with this email already exists.", "warning")
            return render_template('register.html')
            
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, organization, department, contact_phone, bio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, password_hash, role, organization, department, contact_phone, bio))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        session['user_id'] = user_id
        session['user_name'] = name
        session['role'] = role
        session['email'] = email
        
        flash("Account created successfully! Welcome to Project After Life.", "success")
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('company_explorer'))
            
    return render_template('register.html')

@app.route('/demo-login/<role>')
def demo_login(role):
    """Convenience one-click demo login for easy testing."""
    conn = get_db()
    cursor = conn.cursor()
    if role == 'student':
        cursor.execute("SELECT * FROM users WHERE email = 'student@projectafterlife.io'")
    else:
        cursor.execute("SELECT * FROM users WHERE email = 'company@projectafterlife.io'")
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['role'] = user['role']
        session['email'] = user['email']
        flash(f"Signed in as Demo {user['role'].capitalize()} ({user['name']})", "info")
        if user['role'] == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('company_explorer'))
    flash("Demo user not found.", "warning")
    return redirect(url_for('login'))

@app.route('/switch-role/<role>')
@login_required
def switch_role(role):
    """Quickly switch session role for testing interactions between student & company."""
    conn = get_db()
    cursor = conn.cursor()
    if role == 'student':
        cursor.execute("SELECT * FROM users WHERE role = 'student' LIMIT 1")
    else:
        cursor.execute("SELECT * FROM users WHERE role = 'company' LIMIT 1")
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['role'] = user['role']
        session['email'] = user['email']
        flash(f"Switched view to {user['role'].capitalize()}: {user['name']}", "info")
        if user['role'] == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('company_explorer'))
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('index'))


# --- Module 1: Student Project Submission & Student Dashboard ---

def is_valid_github_url(url):
    """Validates GitHub URL format."""
    if not url:
        return False
    # Accepts patterns like https://github.com/owner/repo or http://github.com/owner/repo
    pattern = r'^https?:\/\/(www\.)?github\.com\/[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+.*$'
    return bool(re.match(pattern, url.strip()))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all projects submitted by this student
    cursor.execute("""
        SELECT * FROM projects 
        WHERE student_id = ? 
        ORDER BY created_at DESC
    """, (session['user_id'],))
    projects = cursor.fetchall()
    
    # Get all company interests, funding proposals and approvals for student's projects
    cursor.execute("""
        SELECT pi.*, p.project_title, u.name as company_name, u.organization as company_org, u.email as company_email
        FROM project_interests pi
        JOIN projects p ON pi.project_id = p.id
        JOIN users u ON pi.company_id = u.id
        WHERE p.student_id = ?
        ORDER BY pi.updated_at DESC
    """, (session['user_id'],))
    company_interests = cursor.fetchall()
    
    # Get recent messages from companies
    cursor.execute("""
        SELECT m.*, p.project_title, u.name as sender_user_name, u.organization as sender_org
        FROM messages m
        JOIN projects p ON m.project_id = p.id
        JOIN users u ON m.sender_id = u.id
        WHERE m.recipient_id = ?
        ORDER BY m.created_at DESC LIMIT 10
    """, (session['user_id'],))
    messages = cursor.fetchall()
    
    # Get development progress summary
    cursor.execute("""
        SELECT p.id, p.project_title, p.development_stage, p.progress_percentage, p.funding_status,
               COUNT(m.id) as total_milestones,
               SUM(CASE WHEN m.status = 'Approved by Company' THEN 1 ELSE 0 END) as approved_milestones
        FROM projects p
        LEFT JOIN milestones m ON p.id = m.project_id
        WHERE p.student_id = ? AND p.funding_status = 'Funding Approved'
        GROUP BY p.id
    """, (session['user_id'],))
    active_development_projects = cursor.fetchall()
    
    conn.close()
    
    return render_template('student_dashboard.html',
                           projects=projects,
                           company_interests=company_interests,
                           messages=messages,
                           active_dev_projects=active_development_projects)

@app.route('/project/submit', methods=['GET', 'POST'])
@login_required
def project_submit():
    if request.method == 'POST':
        student_name = request.form.get('student_name', '').strip()
        college_name = request.form.get('college_name', '').strip()
        department = request.form.get('department', '').strip()
        team_members = request.form.get('team_members', '').strip()
        hackathon_name = request.form.get('hackathon_name', '').strip()
        project_title = request.form.get('project_title', '').strip()
        problem_statement = request.form.get('problem_statement', '').strip()
        proposed_solution = request.form.get('proposed_solution', '').strip()
        project_description = request.form.get('project_description', '').strip()
        domain = request.form.get('domain', '').strip()
        technologies_used = request.form.get('technologies_used', '').strip()
        github_url = request.form.get('github_url', '').strip()
        demo_url = request.form.get('demo_url', '').strip()
        documentation_url = request.form.get('documentation_url', '').strip()
        presentation_url = request.form.get('presentation_url', '').strip()
        contact_details = request.form.get('contact_details', '').strip()
        expected_funding_str = request.form.get('expected_funding', '0').replace('$', '').replace(',', '').strip()
        
        try:
            expected_funding = float(expected_funding_str) if expected_funding_str else 0.0
        except ValueError:
            expected_funding = 0.0
            
        # Validation
        errors = []
        if not student_name: errors.append("Student Name is required.")
        if not college_name: errors.append("College Name is required.")
        if not department: errors.append("Department is required.")
        if not hackathon_name: errors.append("Hackathon Name is required.")
        if not project_title: errors.append("Project Title is required.")
        if not problem_statement: errors.append("Problem Statement is required.")
        if not proposed_solution: errors.append("Proposed Solution is required.")
        if not project_description: errors.append("Project Description is required.")
        if not domain: errors.append("Project Domain is required.")
        if not technologies_used: errors.append("Technologies Used is required.")
        if not contact_details: errors.append("Contact Details are required.")
        
        # GitHub URL Validation
        if not github_url:
            errors.append("GitHub Repository Link is required.")
        elif not is_valid_github_url(github_url):
            errors.append("Invalid GitHub repository URL. Must be in the format: https://github.com/username/repository")
            
        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('project_submit.html', form_data=request.form)
            
        # Automatic AI Analysis computation
        project_dict = {
            'project_title': project_title,
            'domain': domain,
            'technologies_used': technologies_used,
            'problem_statement': problem_statement,
            'proposed_solution': proposed_solution,
            'project_description': project_description,
            'github_url': github_url
        }
        ai_data = analyze_project(project_dict)
        ai_analysis_json = json.dumps(ai_data)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO projects (
                student_id, student_name, college_name, department, team_members,
                hackathon_name, project_title, problem_statement, proposed_solution,
                project_description, domain, technologies_used, github_url, demo_url,
                documentation_url, presentation_url, expected_funding, contact_details,
                submission_status, funding_status, development_stage, progress_percentage, ai_analysis_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session['user_id'], student_name, college_name, department, team_members,
            hackathon_name, project_title, problem_statement, proposed_solution,
            project_description, domain, technologies_used, github_url, demo_url,
            documentation_url, presentation_url, expected_funding, contact_details,
            'Submitted', 'None', 'Planning', 0, ai_analysis_json
        ))
        
        project_id = cursor.lastrowid
        
        # Create notification for student
        cursor.execute("""
            INSERT INTO notifications (user_id, project_id, type, title, message)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session['user_id'], project_id, 'submission',
            'Project Submitted Successfully',
            f'Your project "{project_title}" has been submitted and is queued for verification review.'
        ))
        
        conn.commit()
        conn.close()
        
        flash("Project submitted successfully! Status: 'Submitted'. It will now proceed to 'Under Review'.", "success")
        return redirect(url_for('student_dashboard'))
        
    # GET request: prefill from student profile
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    prefill = {
        'student_name': user['name'] if user else '',
        'college_name': user['organization'] if user else '',
        'department': user['department'] if user else '',
        'contact_details': f"{user['email']} | {user['contact_phone']}" if user else ''
    }
    return render_template('project_submit.html', form_data=prefill)

@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(project_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    
    if not project:
        conn.close()
        flash("Project not found.", "warning")
        return redirect(url_for('student_dashboard'))
        
    if project['student_id'] != session['user_id'] and session.get('role') != 'admin':
        conn.close()
        flash("Unauthorized to edit this project.", "danger")
        return redirect(url_for('student_dashboard'))
        
    if request.method == 'POST':
        student_name = request.form.get('student_name', '').strip()
        college_name = request.form.get('college_name', '').strip()
        department = request.form.get('department', '').strip()
        team_members = request.form.get('team_members', '').strip()
        hackathon_name = request.form.get('hackathon_name', '').strip()
        project_title = request.form.get('project_title', '').strip()
        problem_statement = request.form.get('problem_statement', '').strip()
        proposed_solution = request.form.get('proposed_solution', '').strip()
        project_description = request.form.get('project_description', '').strip()
        domain = request.form.get('domain', '').strip()
        technologies_used = request.form.get('technologies_used', '').strip()
        github_url = request.form.get('github_url', '').strip()
        demo_url = request.form.get('demo_url', '').strip()
        documentation_url = request.form.get('documentation_url', '').strip()
        presentation_url = request.form.get('presentation_url', '').strip()
        contact_details = request.form.get('contact_details', '').strip()
        expected_funding_str = request.form.get('expected_funding', '0').replace('$', '').replace(',', '').strip()
        
        try:
            expected_funding = float(expected_funding_str) if expected_funding_str else 0.0
        except ValueError:
            expected_funding = project['expected_funding']
            
        if not is_valid_github_url(github_url):
            flash("Invalid GitHub repository URL. Must be in format: https://github.com/owner/repo", "danger")
            conn.close()
            return render_template('project_edit.html', project=project)
            
        # Recompute AI analysis on update
        ai_data = analyze_project({
            'project_title': project_title,
            'domain': domain,
            'technologies_used': technologies_used,
            'problem_statement': problem_statement,
            'proposed_solution': proposed_solution,
            'project_description': project_description,
            'github_url': github_url
        })
        ai_analysis_json = json.dumps(ai_data)
        
        cursor.execute("""
            UPDATE projects SET
                student_name = ?, college_name = ?, department = ?, team_members = ?,
                hackathon_name = ?, project_title = ?, problem_statement = ?, proposed_solution = ?,
                project_description = ?, domain = ?, technologies_used = ?, github_url = ?,
                demo_url = ?, documentation_url = ?, presentation_url = ?, expected_funding = ?,
                contact_details = ?, ai_analysis_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            student_name, college_name, department, team_members,
            hackathon_name, project_title, problem_statement, proposed_solution,
            project_description, domain, technologies_used, github_url,
            demo_url, documentation_url, presentation_url, expected_funding,
            contact_details, ai_analysis_json, project_id
        ))
        conn.commit()
        conn.close()
        flash("Project updated successfully!", "success")
        return redirect(url_for('student_dashboard'))
        
    conn.close()
    return render_template('project_edit.html', project=project)

@app.route('/project/<int:project_id>/update-submission-status', methods=['POST'])
@login_required
def update_submission_status(project_id):
    """Allows advancing submission status: Submitted -> Under Review -> Approved -> Published"""
    next_status = request.form.get('status')
    valid_statuses = ['Submitted', 'Under Review', 'Approved', 'Published']
    if next_status in valid_statuses:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE projects SET submission_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (next_status, project_id))
        
        # Get project for notification
        cursor.execute("SELECT student_id, project_title FROM projects WHERE id = ?", (project_id,))
        p = cursor.fetchone()
        if p:
            cursor.execute("""
                INSERT INTO notifications (user_id, project_id, type, title, message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                p['student_id'], project_id, 'submission_status',
                f'Project Status: {next_status}',
                f'Your project "{p["project_title"]}" has transitioned to {next_status}.'
            ))
            
        conn.commit()
        conn.close()
        flash(f"Submission status updated to: {next_status}", "success")
    return redirect(request.referrer or url_for('student_dashboard'))


# --- Module 2: Company Project Explorer & AI Analysis ---

@app.route('/company/explorer')
def company_explorer():
    search_q = request.args.get('q', '').strip()
    tech_filter = request.args.get('technology', '').strip()
    domain_filter = request.args.get('domain', '').strip()
    hackathon_filter = request.args.get('hackathon', '').strip()
    college_filter = request.args.get('college', '').strip()
    funding_max = request.args.get('funding_max', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Query all filter values for dropdowns
    cursor.execute("SELECT DISTINCT domain FROM projects WHERE domain != ''")
    domains = [row['domain'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT hackathon_name FROM projects WHERE hackathon_name != ''")
    hackathons = [row['hackathon_name'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT college_name FROM projects WHERE college_name != ''")
    colleges = [row['college_name'] for row in cursor.fetchall()]
    
    # Build query
    sql = """
        SELECT p.*, u.organization as student_college,
               (SELECT COUNT(*) FROM saved_projects sp WHERE sp.project_id = p.id AND sp.company_id = ?) as is_saved,
               (SELECT status FROM project_interests pi WHERE pi.project_id = p.id AND pi.company_id = ?) as my_interest_status
        FROM projects p
        JOIN users u ON p.student_id = u.id
        WHERE 1=1
    """
    company_id = session.get('user_id', 0) if session.get('role') == 'company' else 0
    params = [company_id, company_id]
    
    # If not admin, show projects that are Approved or Published (or all for demo flexibility)
    if not status_filter:
        sql += " AND p.submission_status IN ('Approved', 'Published')"
    else:
        sql += " AND p.submission_status = ?"
        params.append(status_filter)
        
    if search_q:
        sql += """ AND (
            p.project_title LIKE ? OR 
            p.problem_statement LIKE ? OR 
            p.proposed_solution LIKE ? OR 
            p.student_name LIKE ? OR 
            p.college_name LIKE ? OR 
            p.technologies_used LIKE ?
        )"""
        q_wild = f"%{search_q}%"
        params.extend([q_wild, q_wild, q_wild, q_wild, q_wild, q_wild])
        
    if tech_filter:
        sql += " AND p.technologies_used LIKE ?"
        params.append(f"%{tech_filter}%")
        
    if domain_filter:
        sql += " AND p.domain = ?"
        params.append(domain_filter)
        
    if hackathon_filter:
        sql += " AND p.hackathon_name = ?"
        params.append(hackathon_filter)
        
    if college_filter:
        sql += " AND p.college_name = ?"
        params.append(college_filter)
        
    if funding_max:
        try:
            sql += " AND p.expected_funding <= ?"
            params.append(float(funding_max))
        except ValueError:
            pass
            
    sql += " ORDER BY p.created_at DESC"
    
    cursor.execute(sql, params)
    projects = cursor.fetchall()
    
    conn.close()
    
    return render_template('company_explorer.html',
                           projects=projects,
                           domains=domains,
                           hackathons=hackathons,
                           colleges=colleges,
                           filters={
                               'q': search_q,
                               'technology': tech_filter,
                               'domain': domain_filter,
                               'hackathon': hackathon_filter,
                               'college': college_filter,
                               'funding_max': funding_max,
                               'status': status_filter
                           })

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.*, u.name as student_user_name, u.email as student_email, u.organization as student_college, u.bio as student_bio
        FROM projects p
        JOIN users u ON p.student_id = u.id
        WHERE p.id = ?
    """, (project_id,))
    project = cursor.fetchone()
    
    if not project:
        conn.close()
        flash("Project not found.", "warning")
        return redirect(url_for('company_explorer'))
        
    # Parse AI analysis
    ai_analysis = None
    if project['ai_analysis_json']:
        try:
            ai_analysis = json.loads(project['ai_analysis_json'])
        except Exception:
            pass
            
    if not ai_analysis:
        ai_analysis = analyze_project(dict(project))
        
    # Check if company has saved or interacted
    is_saved = False
    current_interest = None
    if session.get('role') == 'company' and 'user_id' in session:
        cursor.execute("SELECT id FROM saved_projects WHERE company_id = ? AND project_id = ?", (session['user_id'], project_id))
        is_saved = bool(cursor.fetchone())
        
        cursor.execute("SELECT * FROM project_interests WHERE company_id = ? AND project_id = ?", (session['user_id'], project_id))
        current_interest = cursor.fetchone()
        
    # Get public milestones preview
    cursor.execute("SELECT * FROM milestones WHERE project_id = ? ORDER BY id ASC", (project_id,))
    milestones = cursor.fetchall()
    
    conn.close()
    
    return render_template('project_detail.html',
                           project=project,
                           ai_analysis=ai_analysis,
                           is_saved=is_saved,
                           current_interest=current_interest,
                           milestones=milestones)

@app.route('/project/<int:project_id>/toggle-save', methods=['POST'])
@login_required
def toggle_save_project(project_id):
    if session.get('role') != 'company':
        return jsonify({'error': 'Only company accounts can save projects'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM saved_projects WHERE company_id = ? AND project_id = ?", (session['user_id'], project_id))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("DELETE FROM saved_projects WHERE id = ?", (existing['id'],))
        is_saved = False
    else:
        cursor.execute("INSERT INTO saved_projects (company_id, project_id) VALUES (?, ?)", (session['user_id'], project_id))
        is_saved = True
        
    conn.commit()
    conn.close()
    return jsonify({'saved': is_saved})


# --- Module 3: Project Selection and Funding Management ---

@app.route('/project/<int:project_id>/evaluate')
@login_required
def project_evaluate(project_id):
    if session.get('role') != 'company' and session.get('role') != 'admin':
        flash("The Project Evaluation panel is reserved for company reviewers.", "warning")
        return redirect(url_for('project_detail', project_id=project_id))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, u.name as student_user_name, u.email as student_email, u.organization as student_college, u.bio as student_bio
        FROM projects p
        JOIN users u ON p.student_id = u.id
        WHERE p.id = ?
    """, (project_id,))
    project = cursor.fetchone()
    
    if not project:
        conn.close()
        flash("Project not found.", "warning")
        return redirect(url_for('company_explorer'))
        
    cursor.execute("SELECT * FROM project_interests WHERE company_id = ? AND project_id = ?", (session['user_id'], project_id))
    interest = cursor.fetchone()
    
    # Get discussion messages
    cursor.execute("""
        SELECT * FROM messages 
        WHERE project_id = ? AND ((sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?))
        ORDER BY created_at ASC
    """, (project_id, session['user_id'], project['student_id'], project['student_id'], session['user_id']))
    messages = cursor.fetchall()
    
    conn.close()
    
    ai_analysis = None
    if project['ai_analysis_json']:
        try:
            ai_analysis = json.loads(project['ai_analysis_json'])
        except Exception:
            pass
    if not ai_analysis:
        ai_analysis = analyze_project(dict(project))
        
    return render_template('project_evaluate.html',
                           project=project,
                           interest=interest,
                           messages=messages,
                           ai_analysis=ai_analysis)

@app.route('/project/<int:project_id>/funding-action', methods=['POST'])
@login_required
def project_funding_action(project_id):
    if session.get('role') != 'company' and session.get('role') != 'admin':
        flash("Only company evaluators can perform funding actions.", "danger")
        return redirect(url_for('project_detail', project_id=project_id))
        
    action = request.form.get('action') # 'shortlist', 'interest', 'propose_funding', 'approve_funding', 'reject_funding', 'request_meeting', 'request_info', 'update_notes'
    company_notes = request.form.get('company_notes', '').strip()
    proposed_amount = request.form.get('proposed_amount', '0').replace('$', '').replace(',', '').strip()
    approved_amount = request.form.get('approved_amount', '0').replace('$', '').replace(',', '').strip()
    meeting_details = request.form.get('meeting_details', '').strip()
    info_query = request.form.get('info_query', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check project exists
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    if not project:
        conn.close()
        flash("Project not found.", "danger")
        return redirect(url_for('company_explorer'))
        
    # Get or create interest record
    cursor.execute("SELECT * FROM project_interests WHERE company_id = ? AND project_id = ?", (session['user_id'], project_id))
    interest = cursor.fetchone()
    
    new_status = interest['status'] if interest else 'Interested'
    p_amount = float(proposed_amount) if proposed_amount else (interest['proposed_amount'] if interest else 0.0)
    a_amount = float(approved_amount) if approved_amount else (interest['approved_amount'] if interest else 0.0)
    funding_date = interest['funding_date'] if interest else None
    
    notif_title = ""
    notif_msg = ""
    
    # Lifecycle: Interested -> Shortlisted -> Discussion -> Funding Proposed -> Funding Approved -> Development Started
    if action == 'interest':
        new_status = 'Interested'
        notif_title = f"{session['user_name']} is interested in your project"
        notif_msg = f"{session['user_name']} expressed interest in '{project['project_title']}'."
    elif action == 'shortlist':
        new_status = 'Shortlisted'
        notif_title = f"Project Shortlisted by {session['user_name']}"
        notif_msg = f"Your project '{project['project_title']}' was shortlisted for funding evaluation."
    elif action == 'propose_funding':
        new_status = 'Funding Proposed'
        p_amount = float(proposed_amount) if proposed_amount else project['expected_funding']
        notif_title = f"Funding Proposal: ${p_amount:,.2f}"
        notif_msg = f"{session['user_name']} proposed funding of ${p_amount:,.2f} for '{project['project_title']}'."
    elif action == 'approve_funding':
        new_status = 'Funding Approved'
        a_amount = float(approved_amount) if approved_amount else (p_amount if p_amount > 0 else project['expected_funding'])
        funding_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        notif_title = f"Funding Approved: ${a_amount:,.2f}!"
        notif_msg = f"Congratulations! {session['user_name']} approved ${a_amount:,.2f} in project funding. Development phase unlocked!"
    elif action == 'reject_funding':
        new_status = 'Rejected'
        notif_title = "Funding Status Update"
        notif_msg = f"{session['user_name']} concluded their evaluation for '{project['project_title']}'."
    elif action == 'request_meeting':
        new_status = 'Discussion'
        notif_title = f"Meeting Request from {session['user_name']}"
        notif_msg = f"Meeting proposal: {meeting_details}"
    elif action == 'request_info':
        new_status = 'Discussion'
        notif_title = f"Additional Information Requested"
        notif_msg = f"{session['user_name']} asked: {info_query}"
        
    if interest:
        cursor.execute("""
            UPDATE project_interests SET
                status = ?,
                proposed_amount = ?,
                approved_amount = ?,
                funding_date = COALESCE(?, funding_date),
                company_notes = COALESCE(NULLIF(?, ''), company_notes),
                meeting_requested = CASE WHEN ? != '' THEN 1 ELSE meeting_requested END,
                meeting_details = COALESCE(NULLIF(?, ''), meeting_details),
                additional_info_requested = CASE WHEN ? != '' THEN 1 ELSE additional_info_requested END,
                additional_info_query = COALESCE(NULLIF(?, ''), additional_info_query),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            new_status, p_amount, a_amount, funding_date, company_notes,
            meeting_details, meeting_details, info_query, info_query, interest['id']
        ))
    else:
        cursor.execute("""
            INSERT INTO project_interests (
                project_id, company_id, status, proposed_amount, approved_amount,
                funding_date, company_notes, meeting_requested, meeting_details,
                additional_info_requested, additional_info_query
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, session['user_id'], new_status, p_amount, a_amount,
            funding_date, company_notes, 1 if meeting_details else 0, meeting_details,
            1 if info_query else 0, info_query
        ))
        
    # Update main project's funding status if promoted
    cursor.execute("""
        UPDATE projects SET
            funding_status = ?,
            development_stage = CASE WHEN ? = 'Funding Approved' THEN 'Planning' ELSE development_stage END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, new_status, project_id))
    
    # Notify student
    if notif_title:
        cursor.execute("""
            INSERT INTO notifications (user_id, project_id, type, title, message)
            VALUES (?, ?, ?, ?, ?)
        """, (project['student_id'], project_id, 'funding_updates', notif_title, notif_msg))
        
    conn.commit()
    conn.close()
    
    flash(f"Action '{action.replace('_', ' ').title()}' completed successfully. Status: {new_status}.", "success")
    return redirect(url_for('project_evaluate', project_id=project_id))

@app.route('/company/funding')
@login_required
def company_funding():
    """Funding Dashboard for Companies (Module 3)"""
    if session.get('role') != 'company' and session.get('role') != 'admin':
        flash("This dashboard is reserved for company accounts.", "warning")
        return redirect(url_for('index'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Clear records of proposed amount, approved amount, funding date, funding status, project status
    cursor.execute("""
        SELECT pi.*, p.project_title, p.domain, p.expected_funding, p.submission_status, p.development_stage, p.progress_percentage,
               u.name as student_name, u.organization as student_college, u.email as student_email
        FROM project_interests pi
        JOIN projects p ON pi.project_id = p.id
        JOIN users u ON p.student_id = u.id
        WHERE pi.company_id = ?
        ORDER BY pi.updated_at DESC
    """, (session['user_id'],))
    funding_records = cursor.fetchall()
    
    # Aggregate metrics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_deals,
            SUM(CASE WHEN status = 'Funding Approved' THEN approved_amount ELSE 0 END) as total_approved_amount,
            SUM(CASE WHEN status = 'Funding Proposed' THEN proposed_amount ELSE 0 END) as total_proposed_amount,
            SUM(CASE WHEN status = 'Funding Approved' THEN 1 ELSE 0 END) as active_funded_count
        FROM project_interests
        WHERE company_id = ?
    """, (session['user_id'],))
    stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('company_funding.html',
                           funding_records=funding_records,
                           stats=stats)


# --- Module 4: Project Development and Progress Tracking ---

@app.route('/project/<int:project_id>/development')
@login_required
def project_development(project_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.*, u.name as student_user_name, u.organization as student_college, u.email as student_email
        FROM projects p
        JOIN users u ON p.student_id = u.id
        WHERE p.id = ?
    """, (project_id,))
    project = cursor.fetchone()
    
    if not project:
        conn.close()
        flash("Project not found.", "warning")
        return redirect(url_for('index'))
        
    # Check access: student owner or company sponsor or admin
    is_owner = (project['student_id'] == session['user_id'])
    
    cursor.execute("SELECT * FROM project_interests WHERE project_id = ? AND company_id = ?", (project_id, session['user_id']))
    company_relation = cursor.fetchone()
    is_sponsor = bool(company_relation)
    
    if not is_owner and not is_sponsor and session.get('role') != 'admin':
        # If public preview is permitted, let them view read-only
        pass
        
    # Fetch milestones
    cursor.execute("""
        SELECT m.*, 
               (SELECT COUNT(*) FROM tasks t WHERE t.milestone_id = m.id) as total_tasks,
               (SELECT COUNT(*) FROM tasks t WHERE t.milestone_id = m.id AND t.is_completed = 1) as completed_tasks
        FROM milestones m 
        WHERE m.project_id = ? 
        ORDER BY m.id ASC
    """, (project_id,))
    milestones = cursor.fetchall()
    
    # Fetch all tasks grouped
    cursor.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY id ASC", (project_id,))
    tasks = cursor.fetchall()
    
    # Fetch progress updates / versions / reports
    cursor.execute("SELECT * FROM progress_updates WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    updates = cursor.fetchall()
    
    conn.close()
    
    # Lifecycle stages definition
    lifecycle_stages = [
        "Funding Approved", "Planning", "Prototype", "Development", 
        "Testing", "Company Review", "Final Product", "Deployment"
    ]
    
    return render_template('project_development.html',
                           project=project,
                           milestones=milestones,
                           tasks=tasks,
                           updates=updates,
                           lifecycle_stages=lifecycle_stages,
                           is_owner=is_owner,
                           is_sponsor=is_sponsor)

@app.route('/project/<int:project_id>/stage-advance', methods=['POST'])
@login_required
def project_stage_advance(project_id):
    new_stage = request.form.get('stage')
    valid_stages = ["Funding Approved", "Planning", "Prototype", "Development", "Testing", "Company Review", "Final Product", "Deployment"]
    
    if new_stage in valid_stages:
        conn = get_db()
        cursor = conn.cursor()
        
        # Calculate dynamic percentage based on stage
        stage_idx = valid_stages.index(new_stage)
        progress_pct = int(((stage_idx) / (len(valid_stages) - 1)) * 100)
        
        cursor.execute("""
            UPDATE projects SET 
                development_stage = ?,
                progress_percentage = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_stage, progress_pct, project_id))
        
        # Notify
        cursor.execute("SELECT student_id, project_title FROM projects WHERE id = ?", (project_id,))
        p = cursor.fetchone()
        if p:
            cursor.execute("""
                INSERT INTO notifications (user_id, project_id, type, title, message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                p['student_id'], project_id, 'task_updates',
                f'Development Stage: {new_stage}',
                f'Project "{p["project_title"]}" advanced to stage {new_stage} ({progress_pct}% overall progress).'
            ))
            
        conn.commit()
        conn.close()
        flash(f"Stage transitioned to: {new_stage} ({progress_pct}%)", "success")
        
    return redirect(url_for('project_development', project_id=project_id))

@app.route('/milestone/create', methods=['POST'])
@login_required
def milestone_create():
    project_id = request.form.get('project_id')
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    target_date = request.form.get('target_date', '').strip()
    stage = request.form.get('stage', 'Development')
    
    if not title:
        flash("Milestone title is required.", "danger")
        return redirect(url_for('project_development', project_id=project_id))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO milestones (project_id, title, description, target_date, stage, status)
        VALUES (?, ?, ?, ?, ?, 'In Progress')
    """, (project_id, title, description, target_date, stage))
    
    # Notify company sponsors
    cursor.execute("SELECT company_id FROM project_interests WHERE project_id = ? AND status = 'Funding Approved'", (project_id,))
    sponsors = cursor.fetchall()
    for sp in sponsors:
        cursor.execute("""
            INSERT INTO notifications (user_id, project_id, type, title, message)
            VALUES (?, ?, ?, ?, ?)
        """, (
            sp['company_id'], project_id, 'new_milestone',
            'New Milestone Created',
            f'Student team created new milestone: "{title}"'
        ))
        
    conn.commit()
    conn.close()
    
    flash("New milestone created successfully!", "success")
    return redirect(url_for('project_development', project_id=project_id))

@app.route('/milestone/<int:milestone_id>/action', methods=['POST'])
@login_required
def milestone_action(milestone_id):
    action = request.form.get('action') # 'submit_completed', 'approve', 'request_changes', 'comment'
    feedback = request.form.get('feedback', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM milestones WHERE id = ?", (milestone_id,))
    m = cursor.fetchone()
    if not m:
        conn.close()
        flash("Milestone not found.", "warning")
        return redirect(request.referrer)
        
    project_id = m['project_id']
    cursor.execute("SELECT student_id, project_title FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    
    if action == 'submit_completed':
        cursor.execute("""
            UPDATE milestones SET status = 'Completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (milestone_id,))
        # Notify company
        cursor.execute("SELECT company_id FROM project_interests WHERE project_id = ?", (project_id,))
        sponsors = cursor.fetchall()
        for sp in sponsors:
            cursor.execute("""
                INSERT INTO notifications (user_id, project_id, type, title, message)
                VALUES (?, ?, ?, ?, ?)
            """, (sp['company_id'], project_id, 'milestone_completed', f'Milestone Completed: {m["title"]}', f'Team submitted completed milestone for review.'))
        flash("Milestone submitted for company verification.", "success")
        
    elif action == 'approve':
        cursor.execute("""
            UPDATE milestones SET status = 'Approved by Company', company_feedback = ? WHERE id = ?
        """, (feedback, milestone_id))
        cursor.execute("""
            INSERT INTO notifications (user_id, project_id, type, title, message)
            VALUES (?, ?, ?, ?, ?)
        """, (project['student_id'], project_id, 'company_feedback', f'Milestone Approved: {m["title"]}', f'Feedback: {feedback}'))
        flash("Milestone approved with company feedback!", "success")
        
    elif action == 'request_changes':
        cursor.execute("""
            UPDATE milestones SET status = 'Changes Requested', company_feedback = ? WHERE id = ?
        """, (feedback, milestone_id))
        cursor.execute("""
            INSERT INTO notifications (user_id, project_id, type, title, message)
            VALUES (?, ?, ?, ?, ?)
        """, (project['student_id'], project_id, 'company_feedback', f'Changes Requested: {m["title"]}', f'Action items: {feedback}'))
        flash("Change request submitted to student team.", "warning")
        
    conn.commit()
    conn.close()
    return redirect(url_for('project_development', project_id=project_id))

@app.route('/task/create', methods=['POST'])
@login_required
def task_create():
    milestone_id = request.form.get('milestone_id')
    project_id = request.form.get('project_id')
    title = request.form.get('title', '').strip()
    assigned_to = request.form.get('assigned_to', '').strip()
    
    if title:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (milestone_id, project_id, title, is_completed, assigned_to)
            VALUES (?, ?, ?, 0, ?)
        """, (milestone_id, project_id, title, assigned_to))
        conn.commit()
        conn.close()
        flash("Task added to milestone.", "success")
        
    return redirect(url_for('project_development', project_id=project_id))

@app.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def task_toggle(task_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    if task:
        new_state = 0 if task['is_completed'] else 1
        cursor.execute("UPDATE tasks SET is_completed = ? WHERE id = ?", (new_state, task_id))
        conn.commit()
    conn.close()
    return jsonify({'completed': bool(new_state) if task else False})

@app.route('/progress/upload', methods=['POST'])
@login_required
def progress_upload():
    """Upload project versions, update GitHub commits, progress reports, screenshots, demo videos"""
    project_id = request.form.get('project_id')
    version_tag = request.form.get('version_tag', '').strip()
    github_commit_or_branch = request.form.get('github_commit_or_branch', '').strip()
    report_text = request.form.get('report_text', '').strip()
    demo_video_url = request.form.get('demo_video_url', '').strip()
    screenshot_url = request.form.get('screenshot_url', '').strip()
    
    screenshots_json = json.dumps([screenshot_url]) if screenshot_url else '[]'
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO progress_updates (
            project_id, version_tag, github_commit_or_branch, report_text, screenshot_urls, demo_video_url
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (project_id, version_tag, github_commit_or_branch, report_text, screenshots_json, demo_video_url))
    
    # Notify company
    cursor.execute("SELECT company_id FROM project_interests WHERE project_id = ?", (project_id,))
    sponsors = cursor.fetchall()
    for sp in sponsors:
        cursor.execute("""
            INSERT INTO notifications (user_id, project_id, type, title, message)
            VALUES (?, ?, ?, ?, ?)
        """, (
            sp['company_id'], project_id, 'task_updates',
            f'New Project Build Released: {version_tag}',
            f'Student team posted progress report & commit updates ({github_commit_or_branch}).'
        ))
        
    conn.commit()
    conn.close()
    flash(f"Build update '{version_tag}' logged successfully!", "success")
    return redirect(url_for('project_development', project_id=project_id))


# --- Discussions / Messages & Notifications ---

@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    project_id = request.form.get('project_id')
    recipient_id = request.form.get('recipient_id')
    message_text = request.form.get('message', '').strip()
    
    if message_text and recipient_id:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (project_id, sender_id, sender_name, sender_role, recipient_id, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, session['user_id'], session['user_name'], session.get('role', 'student'), recipient_id, message_text))
        
        # Notification
        cursor.execute("""
            INSERT INTO notifications (user_id, project_id, type, title, message)
            VALUES (?, ?, ?, ?, ?)
        """, (
            recipient_id, project_id, 'company_feedback' if session.get('role') == 'company' else 'task_updates',
            f'New Message from {session["user_name"]}',
            message_text[:100] + ('...' if len(message_text) > 100 else '')
        ))
        
        conn.commit()
        conn.close()
        flash("Message sent.", "success")
        
    return redirect(request.referrer or url_for('student_dashboard'))

@app.route('/notifications')
@login_required
def notifications_view():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.*, p.project_title 
        FROM notifications n
        LEFT JOIN projects p ON n.project_id = p.id
        WHERE n.user_id = ?
        ORDER BY n.created_at DESC
    """, (session['user_id'],))
    all_notifs = cursor.fetchall()
    
    # Mark all read
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (session['user_id'],))
    conn.commit()
    conn.close()
    
    return render_template('notifications.html', notifications=all_notifs)


# --- Inbuilt AI Chatbot API ---

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    role = data.get('role') or session.get('role') or 'student'
    project_id = data.get('project_id')
    
    if not user_message:
        return jsonify({'reply': 'Please type a question or prompt to ask the AI assistant.'})
        
    project_data = None
    if project_id:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            project_data = dict(row)
            
    reply = chat_reply(user_message, role=role, project=project_data)
    
    # Provide contextual suggested follow-ups
    if role == 'student':
        suggested = [
            "How do I write an impactful problem statement?",
            "How should I explain our proposed solution?",
            "How do I add and validate my GitHub repository?",
            "How do I prepare for company questions?",
            "What development milestones should I create?"
        ]
    else:
        suggested = [
            "What problem does this project solve?",
            "What technologies are used in this project?",
            "How can this project be used in our industry?",
            "What questions should we ask the student team?",
            "How do we propose and approve milestone funding?"
        ]
        
    return jsonify({
        'reply': reply,
        'suggested_questions': suggested
    })

if __name__ == '__main__':
    init_db()
    seed_sample_data()
    print("Starting Project After Life Platform...")
    app.run(host='0.0.0.0', port=5000, debug=True)

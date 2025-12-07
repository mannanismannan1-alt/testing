import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.sql import func

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-change-this-in-production")

# Instance folder create karen - absolute path use karen
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

# Database path - absolute path use karen
DB_PATH = os.path.join(INSTANCE_DIR, 'dalildocs.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Upload folders create karen
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pdf_topics'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'ref_topics'), exist_ok=True)

db = SQLAlchemy(app)

# ===================== DATABASE MODELS =====================

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_main = db.Column(db.Boolean, default=False)
    device_id = db.Column(db.Text, default='')

class PdfCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdfs = db.relationship('Pdf', backref='category', lazy=True, cascade='all, delete-orphan')

class Pdf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('pdf_category.id'), nullable=False)
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReferenceTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    references = db.relationship('Reference', backref='topic', lazy=True, cascade='all, delete-orphan')

class Reference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('reference_topic.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(200), nullable=False)
    question = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')
    reply_message = db.Column(db.Text)
    reply_reference = db.Column(db.Text)
    replied_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    reference_id = db.Column(db.Integer, db.ForeignKey('reference.id'), nullable=False)
    reference = db.relationship('Reference', backref='bookmarks')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ===================== HELPER FUNCTIONS =====================

def is_admin_logged_in():
    return 'admin_id' in session

def get_or_create_user_id():
    if 'user_id' not in session:
        session['user_id'] = os.urandom(16).hex()
    return session['user_id']

# ===================== PUBLIC ROUTES =====================

@app.route('/uploads/<folder>/<filename>')
def serve_upload(folder, filename):
    allowed_folders = ['pdf_topics', 'ref_topics', 'pdfs']
    if folder not in allowed_folders:
        abort(404)
    from werkzeug.utils import safe_join
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    return send_from_directory(upload_dir, filename)

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/')
def home():
    stats = {
        'pdf_count': Pdf.query.count(),
        'ref_count': Reference.query.count(),
        'pdf_categories': PdfCategory.query.count(),
        'ref_topics': ReferenceTopic.query.count()
    }
    popular_pdfs = Pdf.query.order_by(Pdf.view_count.desc()).limit(6).all()
    popular_refs = Reference.query.order_by(Reference.view_count.desc()).limit(6).all()
    
    return render_template('home.html', 
                         pdf_count=stats['pdf_count'],
                         ref_count=stats['ref_count'],
                         pdf_categories=stats['pdf_categories'],
                         ref_topics=stats['ref_topics'],
                         popular_pdfs=popular_pdfs,
                         popular_refs=popular_refs)

@app.route('/pdfs')
def pdfs():
    sort = request.args.get('sort', 'newest')
    categories = PdfCategory.query
    
    if sort == 'popular':
        categories = categories.order_by(PdfCategory.view_count.desc())
    elif sort == 'az':
        categories = categories.order_by(PdfCategory.name.asc())
    else:
        categories = categories.order_by(PdfCategory.created_at.desc())
    
    categories = categories.all()
    return render_template('pdfs.html', categories=categories, sort=sort)

@app.route('/references')
def references():
    sort = request.args.get('sort', 'newest')
    topics = ReferenceTopic.query
    
    if sort == 'popular':
        topics = topics.order_by(ReferenceTopic.view_count.desc())
    elif sort == 'az':
        topics = topics.order_by(ReferenceTopic.name.asc())
    else:
        topics = topics.order_by(ReferenceTopic.created_at.desc())
    
    topics = topics.all()
    return render_template('references.html', topics=topics, sort=sort)

@app.route('/ask_us', methods=['GET', 'POST'])
def ask_us():
    if request.method == 'POST':
        name = request.form.get('name')
        question_text = request.form.get('question')
        new_question = Question(user_name=name, question=question_text)
        db.session.add(new_question)
        db.session.commit()
        flash('✅ Aap ka sawal bhej diya gaya hai', 'success')
        return redirect(url_for('ask_us'))
    return render_template('ask_us.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    sort = request.args.get('sort', 'newest')
    
    pdfs = []
    references = []
    categories = []
    topics = []
    
    if query:
        search_pattern = f"%{query}%"
        
        if search_type in ['all', 'pdfs']:
            pdfs = Pdf.query.filter(Pdf.title.ilike(search_pattern)).all()
            categories = PdfCategory.query.filter(PdfCategory.name.ilike(search_pattern)).all()
        
        if search_type in ['all', 'references']:
            references = Reference.query.filter(
                db.or_(Reference.title.ilike(search_pattern), Reference.content.ilike(search_pattern))
            ).all()
            topics = ReferenceTopic.query.filter(ReferenceTopic.name.ilike(search_pattern)).all()
    
    return render_template('search.html', 
                         query=query, 
                         pdfs=pdfs, 
                         references=references,
                         categories=categories,
                         topics=topics,
                         search_type=search_type,
                         sort=sort)

@app.route('/pdf/<int:pdf_id>')
def view_pdf(pdf_id):
    pdf = Pdf.query.get_or_404(pdf_id)
    pdf.view_count = (pdf.view_count or 0) + 1
    db.session.commit()
    return render_template('pdf_viewer.html', pdf=pdf)

@app.route('/pdf/<int:pdf_id>/download')
def download_pdf(pdf_id):
    pdf = Pdf.query.get_or_404(pdf_id)
    pdf.download_count = (pdf.download_count or 0) + 1
    db.session.commit()
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', pdf.filename)
    return send_file(file_path, as_attachment=True, download_name=pdf.title + '.pdf')

@app.route('/pdf/category/<int:category_id>')
def pdf_category(category_id):
    category = PdfCategory.query.get_or_404(category_id)
    category.view_count = (category.view_count or 0) + 1
    db.session.commit()
    
    sort = request.args.get('sort', 'newest')
    pdfs = category.pdfs
    
    if sort == 'popular':
        pdfs = sorted(pdfs, key=lambda x: x.view_count or 0, reverse=True)
    elif sort == 'az':
        pdfs = sorted(pdfs, key=lambda x: x.title)
    else:
        pdfs = sorted(pdfs, key=lambda x: x.uploaded_at, reverse=True)
    
    return render_template('pdf_category.html', category=category, pdfs=pdfs, sort=sort)

@app.route('/reference/<int:ref_id>')
def view_reference(ref_id):
    reference = Reference.query.get_or_404(ref_id)
    reference.view_count = (reference.view_count or 0) + 1
    db.session.commit()
    
    return render_template('reference_detail.html', reference=reference)

@app.route('/topic/<int:topic_id>')
def topic_references(topic_id):
    topic = ReferenceTopic.query.get_or_404(topic_id)
    topic.view_count = (topic.view_count or 0) + 1
    db.session.commit()
    
    sort = request.args.get('sort', 'newest')
    references = topic.references
    
    if sort == 'popular':
        references = sorted(references, key=lambda x: x.view_count or 0, reverse=True)
    elif sort == 'az':
        references = sorted(references, key=lambda x: x.title)
    else:
        references = sorted(references, key=lambda x: x.created_at, reverse=True)
    
    return render_template('topic_references.html', topic=topic, references=references, sort=sort)

@app.route('/bookmarks')
def bookmarks():
    user_id = get_or_create_user_id()
    bookmarks = Bookmark.query.filter_by(user_id=user_id).order_by(Bookmark.created_at.desc()).all()
    return render_template('bookmarks.html', bookmarks=bookmarks)

@app.route('/bookmark/<int:ref_id>', methods=['POST'])
def toggle_bookmark(ref_id):
    user_id = get_or_create_user_id()
    bookmark = Bookmark.query.filter_by(user_id=user_id, reference_id=ref_id).first()
    
    if bookmark:
        db.session.delete(bookmark)
        flash('❌ Bookmark hata diya gaya', 'success')
    else:
        new_bookmark = Bookmark(user_id=user_id, reference_id=ref_id)
        db.session.add(new_bookmark)
        flash('✅ Bookmark add ho gaya', 'success')
    
    db.session.commit()
    return redirect(request.referrer or url_for('references'))

@app.route('/my_questions/<user_name>')
def my_questions(user_name):
    questions = Question.query.filter_by(user_name=user_name).order_by(Question.created_at.desc()).all()
    return render_template('my_questions.html', questions=questions, user_name=user_name)

# ===================== ADMIN ROUTES =====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('✅ Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid credentials', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    session.pop('manage_admins_verified', None)
    flash('✅ Logout successful', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    admin = Admin.query.get(session['admin_id'])
    
    pdf_views = db.session.query(func.sum(Pdf.view_count)).scalar() or 0
    ref_views = db.session.query(func.sum(Reference.view_count)).scalar() or 0
    
    stats = {
        'total_pdfs': Pdf.query.count(),
        'pdf_categories': PdfCategory.query.count(),
        'total_references': Reference.query.count(),
        'ref_topics': ReferenceTopic.query.count(),
        'pending_questions': Question.query.filter_by(status='pending').count(),
        'total_questions': Question.query.count(),
        'total_views': pdf_views + ref_views,
        'pdf_views': pdf_views,
        'ref_views': ref_views,
        'total_downloads': db.session.query(func.sum(Pdf.download_count)).scalar() or 0,
        'total_bookmarks': Bookmark.query.count()
    }
    
    popular_pdfs = Pdf.query.order_by(Pdf.view_count.desc()).limit(5).all()
    popular_refs = Reference.query.order_by(Reference.view_count.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         admin=admin,
                         popular_pdfs=popular_pdfs,
                         popular_refs=popular_refs)

# ===================== ADMIN PDF MANAGEMENT =====================

@app.route('/admin/pdfs', methods=['GET', 'POST'])
def admin_pdfs():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_category':
            name = request.form.get('category_name')
            description = request.form.get('category_description', '')
            image_filename = None
            
            if 'category_image' in request.files:
                file = request.files['category_image']
                if file and file.filename:
                    ext = file.filename.rsplit('.', 1)[-1].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        filename = secure_filename(file.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf_topics', unique_filename)
                        file.save(file_path)
                        image_filename = unique_filename
            
            new_category = PdfCategory(name=name, description=description, image=image_filename)
            db.session.add(new_category)
            db.session.commit()
            flash('✅ Category shamil ho gayi', 'success')

        elif action == 'add_pdf':
            category_id = request.form.get('category_id')
            title = request.form.get('title') or request.form.get('pdf_title')
            
            # Handle empty category_id - convert to None for PostgreSQL
            if category_id == '' or category_id is None:
                category_id = None
            else:
                category_id = int(category_id)
            
            if 'pdf_file' in request.files:
                file = request.files['pdf_file']
                if file and file.filename and file.filename.endswith('.pdf'):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', unique_filename)
                    file.save(file_path)
                    
                    # Use filename as title if title is not provided
                    if not title:
                        title = filename.rsplit('.', 1)[0]
                    
                    new_pdf = Pdf(title=title, filename=unique_filename, category_id=category_id)
                    db.session.add(new_pdf)
                    db.session.commit()
                    flash('✅ PDF shamil ho gayi', 'success')

        elif action == 'bulk_upload':
            category_id = request.form.get('bulk_category_id')
            
            # Handle empty category_id
            if category_id == '' or category_id is None:
                category_id = None
            else:
                category_id = int(category_id)
            
            if 'bulk_pdfs' in request.files:
                files = request.files.getlist('bulk_pdfs')
                uploaded_count = 0
                
                for file in files:
                    if file and file.filename and file.filename.endswith('.pdf'):
                        filename = secure_filename(file.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', unique_filename)
                        file.save(file_path)
                        
                        # Use filename as title
                        title = filename.rsplit('.', 1)[0]
                        
                        new_pdf = Pdf(title=title, filename=unique_filename, category_id=category_id)
                        db.session.add(new_pdf)
                        uploaded_count += 1
                
                if uploaded_count > 0:
                    db.session.commit()
                    flash(f'✅ {uploaded_count} PDFs shamil ho gayin', 'success')
                else:
                    flash('❌ Koi PDF select nahi ki gayi', 'danger')

    categories = PdfCategory.query.order_by(PdfCategory.created_at.desc()).all()
    pdfs = Pdf.query.order_by(Pdf.uploaded_at.desc()).all()
    return render_template('admin_pdfs.html', categories=categories, pdfs=pdfs)

@app.route('/admin/edit_pdf_category/<int:cat_id>', methods=['GET', 'POST'])
def edit_pdf_category(cat_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    category = PdfCategory.query.get_or_404(cat_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description', '')
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    if category.image:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf_topics', category.image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    filename = secure_filename(file.filename)
                    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf_topics', unique_filename)
                    file.save(file_path)
                    category.image = unique_filename
        
        db.session.commit()
        flash('✅ Category update ho gayi', 'success')
        return redirect(url_for('admin_pdfs'))
    
    return render_template('edit_pdf_category.html', category=category)

@app.route('/admin/edit_pdf/<int:pdf_id>', methods=['GET', 'POST'])
def edit_pdf(pdf_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    pdf = Pdf.query.get_or_404(pdf_id)
    categories = PdfCategory.query.all()
    
    if request.method == 'POST':
        pdf.title = request.form.get('title')
        pdf.category_id = request.form.get('category_id') or None
        db.session.commit()
        flash('✅ PDF update ho gayi', 'success')
        return redirect(url_for('admin_pdfs'))
    
    return render_template('edit_pdf.html', pdf=pdf, categories=categories)

@app.route('/admin/delete_pdf/<int:pdf_id>', methods=['POST'])
def delete_pdf(pdf_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    pdf = Pdf.query.get_or_404(pdf_id)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', pdf.filename)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    
    db.session.delete(pdf)
    db.session.commit()
    flash('✅ PDF hazf ho gayi', 'success')
    return redirect(url_for('admin_pdfs'))

@app.route('/admin/delete_pdf_category/<int:cat_id>', methods=['POST'])
def delete_pdf_category(cat_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    category = PdfCategory.query.get_or_404(cat_id)
    
    if category.image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf_topics', category.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    for pdf in category.pdfs:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', pdf.filename)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    db.session.delete(category)
    db.session.commit()
    flash('✅ Category aur sab PDFs hazf ho gayin', 'success')
    return redirect(url_for('admin_pdfs'))

# ===================== ADMIN REFERENCE MANAGEMENT =====================

@app.route('/admin/references', methods=['GET', 'POST'])
def admin_references():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_topic':
            name = request.form.get('topic_name')
            description = request.form.get('topic_description', '')
            image_filename = None
            
            if 'topic_image' in request.files:
                file = request.files['topic_image']
                if file and file.filename:
                    ext = file.filename.rsplit('.', 1)[-1].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        filename = secure_filename(file.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ref_topics', unique_filename)
                        file.save(file_path)
                        image_filename = unique_filename
            
            new_topic = ReferenceTopic(name=name, description=description, image=image_filename)
            db.session.add(new_topic)
            db.session.commit()
            flash('✅ Topic shamil ho gaya', 'success')

        elif action == 'add_reference':
            topic_id = request.form.get('topic_id')
            ref_title = request.form.get('ref_title')
            ref_content = request.form.get('ref_content')

            new_ref = Reference(topic_id=topic_id, title=ref_title, content=ref_content)
            db.session.add(new_ref)
            db.session.commit()
            flash('✅ Hawala shamil ho gaya', 'success')

    topics = ReferenceTopic.query.order_by(ReferenceTopic.created_at.desc()).all()
    references = Reference.query.order_by(Reference.created_at.desc()).all()
    return render_template('admin_references.html', topics=topics, references=references)

@app.route('/admin/edit_ref_topic/<int:topic_id>', methods=['GET', 'POST'])
def edit_ref_topic(topic_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    topic = ReferenceTopic.query.get_or_404(topic_id)
    
    if request.method == 'POST':
        topic.name = request.form.get('name')
        topic.description = request.form.get('description', '')
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    if topic.image:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ref_topics', topic.image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    filename = secure_filename(file.filename)
                    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ref_topics', unique_filename)
                    file.save(file_path)
                    topic.image = unique_filename
        
        db.session.commit()
        flash('✅ Topic update ho gaya', 'success')
        return redirect(url_for('admin_references'))
    
    return render_template('edit_ref_topic.html', topic=topic)

@app.route('/admin/edit_reference/<int:ref_id>', methods=['GET', 'POST'])
def edit_reference(ref_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    reference = Reference.query.get_or_404(ref_id)
    topics = ReferenceTopic.query.all()
    
    if request.method == 'POST':
        reference.title = request.form.get('title')
        reference.content = request.form.get('content')
        reference.topic_id = request.form.get('topic_id')
        db.session.commit()
        flash('✅ Hawala update ho gaya', 'success')
        return redirect(url_for('admin_references'))
    
    return render_template('edit_reference.html', reference=reference, topics=topics)

@app.route('/admin/delete_reference/<int:ref_id>', methods=['POST'])
def delete_reference(ref_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    reference = Reference.query.get_or_404(ref_id)
    Bookmark.query.filter_by(reference_id=ref_id).delete()
    db.session.delete(reference)
    db.session.commit()

    flash('✅ Hawala hazf ho gaya', 'success')
    return redirect(url_for('admin_references'))

@app.route('/admin/delete_ref_topic/<int:topic_id>', methods=['POST'])
def delete_ref_topic(topic_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    topic = ReferenceTopic.query.get_or_404(topic_id)
    
    if topic.image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ref_topics', topic.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    for ref in topic.references:
        Bookmark.query.filter_by(reference_id=ref.id).delete()

    db.session.delete(topic)
    db.session.commit()
    flash('✅ Topic aur sab hawale hazf ho gaye', 'success')
    return redirect(url_for('admin_references'))

# ===================== ADMIN QUESTIONS =====================

@app.route('/admin/questions')
def admin_questions():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('admin_questions.html', questions=questions)

@app.route('/admin/reply/<int:question_id>', methods=['GET', 'POST'])
def admin_reply(question_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        reply_message = request.form.get('reply_message')
        reply_reference = request.form.get('reply_reference')

        question.reply_message = reply_message
        question.reply_reference = reply_reference
        question.status = 'answered'
        question.replied_at = datetime.utcnow()

        db.session.commit()
        flash('✅ Jawab bhej diya gaya', 'success')
        return redirect(url_for('admin_questions'))

    return render_template('admin_reply.html', question=question)

@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash('✅ Sawal hazf ho gaya', 'success')
    return redirect(url_for('admin_questions'))

# ===================== ADMIN MANAGEMENT =====================

@app.route('/admin/manage_admins', methods=['GET', 'POST'])
def manage_admins():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    admin = Admin.query.get(session['admin_id'])
    if not admin.is_main:
        flash('Sirf main admin is page tak rasai kar sakta hai', 'danger')
        return redirect(url_for('admin_dashboard'))

    if not session.get('manage_admins_verified'):
        if request.method == 'POST' and request.form.get('action') == 'verify':
            verify_password = request.form.get('verify_password')
            main_admin = Admin.query.filter_by(is_main=True).first()
            if main_admin and check_password_hash(main_admin.password, verify_password):
                session['manage_admins_verified'] = True
            else:
                flash('Ghalat password', 'danger')
                return render_template('manage_admins.html', admins=[], need_verification=True)
        else:
            return render_template('manage_admins.html', admins=[], need_verification=True)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            username = request.form.get('username')
            password = request.form.get('password')
            if Admin.query.filter_by(username=username).first():
                flash('Yeh username pehle se mojood hai', 'danger')
            else:
                new_admin = Admin(username=username, password=generate_password_hash(password), is_main=False)
                db.session.add(new_admin)
                db.session.commit()
                flash(f'✅ Admin "{username}" shamil ho gaya', 'success')

        elif action == 'delete':
            admin_id = request.form.get('admin_id')
            admin_to_delete = Admin.query.get(admin_id)
            if admin_to_delete and not admin_to_delete.is_main:
                db.session.delete(admin_to_delete)
                db.session.commit()
                flash('✅ Admin hazf ho gaya', 'success')

        elif action == 'reset_password':
            admin_id = request.form.get('admin_id')
            admin_to_reset = Admin.query.get(admin_id)
            if admin_to_reset and not admin_to_reset.is_main:
                import random
                import string
                new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                admin_to_reset.password = generate_password_hash(new_password)
                db.session.commit()
                flash(f'✅ {admin_to_reset.username} ka naya password: {new_password}', 'success')

    all_admins = Admin.query.all()
    return render_template('manage_admins.html', admins=all_admins, need_verification=False)

@app.route('/admin/change_password', methods=['GET', 'POST'])
def change_password():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    admin = Admin.query.get(session['admin_id'])
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not check_password_hash(admin.password, current_password):
            flash('Mojooda password ghalat hai', 'danger')
        elif new_password != confirm_password:
            flash('Naya password match nahi karta', 'danger')
        elif len(new_password) < 6:
            flash('Password kam az kam 6 characters ka hona chahiye', 'danger')
        else:
            admin.password = generate_password_hash(new_password)
            db.session.commit()
            flash('✅ Password tabdeel ho gaya', 'success')
            return redirect(url_for('admin_dashboard'))
    
    return render_template('change_password.html', admin=admin)

# ===================== DATABASE INITIALIZATION =====================

def init_database():
    """Database initialization - ek baar me saari setup"""
    with app.app_context():
        try:
            # Pehle check karen ke tables hain ya nahi
            db.create_all()
            print("✅ Database tables create ho gaye!")
            
            # Main admin check karen
            main_admin = Admin.query.filter_by(is_main=True).first()
            if not main_admin:
                # Default main admin banayen
                main_admin = Admin(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    is_main=True
                )
                db.session.add(main_admin)
                db.session.commit()
                print("\n" + "="*50)
                print("✅ DATABASE SUCCESSFULLY INITIALIZED!")
                print("="*50)
                print("\n📝 DEFAULT ADMIN CREDENTIALS:")
                print("   Username: admin")
                print("   Password: admin123")
                print("\n⚠️  IMPORTANT: Change password after first login!")
                print("="*50 + "\n")
            else:
                print("✅ Main admin already exists")
                
        except Exception as e:
            print(f"❌ Database initialization error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    # Database initialize karen
    init_database()
    
    # Application start karen
    app.run(host='0.0.0.0', port=21179, debug=True)

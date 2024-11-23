from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import time
from PIL import Image
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB макс размер файла
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'avatars')

# Создаем папку для аватаров, если её нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Копируем стандартный аватар, если его нет
default_avatar = os.path.join(app.config['UPLOAD_FOLDER'], 'default.jpg')
if not os.path.exists(default_avatar):
    # Создаем пустое изображение 200x200 серого цвета
    img = Image.new('RGB', (200, 200), color='#cccccc')
    # Сохраняем как default.jpg
    img.save(default_avatar)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_IMAGE_SIZE = (300, 300)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_avatar(file):
    # Читаем изображение
    image = Image.open(file)
    
    # Конвертируем в RGB если нужно
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Изменяем размер, сохраняя пропорции
    image.thumbnail(MAX_IMAGE_SIZE)
    
    # Создаем буфер для сохранения
    img_buffer = io.BytesIO()
    
    # Сохраняем с оптимизацией качества
    image.save(img_buffer, format='JPEG', quality=85, optimize=True)
    
    return img_buffer.getvalue()

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    date_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    # Новые поля для профиля
    avatar = db.Column(db.String(200), nullable=True, default='avatars/default.jpg')
    bio = db.Column(db.Text, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(200), nullable=True)

    def get_posts_count(self):
        return len(self.posts)

    def get_comments_count(self):
        return len(self.comments)

    def update_last_seen(self):
        self.last_seen = datetime.utcnow()
        db.session.commit()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('home.html', posts=posts)

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post = Post(title=title, content=content, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Ваш пост успешно создан!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html')

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            email=email,
            password=password,
            avatar='avatars/default.jpg'  # Явно устанавливаем стандартный аватар
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Добро пожаловать!', 'success')
            return redirect(url_for('home'))
        flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html')

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    if content:
        comment = Comment(content=content, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен!', 'success')
    return redirect(url_for('post', post_id=post_id))

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        flash('У вас нет прав для удаления этого поста', 'danger')
        return redirect(url_for('post', post_id=post_id))
    db.session.delete(post)
    db.session.commit()
    flash('Пост удален!', 'success')
    return redirect(url_for('home'))

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        flash('У вас нет прав для редактирования этого поста', 'danger')
        return redirect(url_for('post', post_id=post_id))
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Пост обновлен!', 'success')
        return redirect(url_for('post', post_id=post_id))
    
    return render_template('edit_post.html', post=post)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).all()
    if current_user.is_authenticated and current_user.username == username:
        user.update_last_seen()
    return render_template('profile.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio')
        current_user.location = request.form.get('location')
        current_user.website = request.form.get('website')
        
        avatar = request.files.get('avatar')
        if avatar and allowed_file(avatar.filename):
            try:
                # Обрабатываем и сохраняем аватар
                processed_image = process_avatar(avatar)
                
                # Генерируем уникальное имя файла
                filename = secure_filename(f"{current_user.username}_{int(time.time())}.jpg")
                avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Сохраняем обработанное изображение
                with open(avatar_path, 'wb') as f:
                    f.write(processed_image)
                
                # Обновляем путь к аватару в базе данных
                current_user.avatar = f"avatars/{filename}"
                
                flash('Аватар успешно обновлен!', 'success')
            except Exception as e:
                flash('Ошибка при обработке изображения. Попробуйте другой файл.', 'danger')
        
        db.session.commit()
        flash('Профиль успешно обновлен!', 'success')
        return redirect(url_for('profile', username=current_user.username))
    
    return render_template('edit_profile.html')

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.update_last_seen()

def create_admin():
    with app.app_context():
        # Проверяем существование админа по имени или email
        admin = User.query.filter(
            (User.username == 'admin') | 
            (User.email == 'admin@example.com')
        ).first()
        
        if admin:
            # Если пользователь существует, делаем его админом
            if not admin.is_admin:
                admin.is_admin = True
                db.session.commit()
        else:
            # Создаем нового админа
            admin = User(
                username='admin',
                email='admin@example.com',
                password='123456',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к панели администратора', 'danger')
        return redirect(url_for('home'))
    users = User.query.all()
    posts = Post.query.all()
    comments = Comment.query.all()
    return render_template('admin.html', users=users, posts=posts, comments=comments)

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Невозможно удалить администратора', 'danger')
        return redirect(url_for('admin_panel'))
    
    # Удаляем все посты и комментарии пользователя
    Post.query.filter_by(user_id=user.id).delete()
    Comment.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь успешно удален', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Вы не можете изменить свои права администратора', 'danger')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"{'Права администратора добавлены' if user.is_admin else 'Права администратора удалены'}", 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/post/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    if not current_user.is_admin:
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('home'))
    
    post = Post.query.get_or_404(post_id)
    Comment.query.filter_by(post_id=post.id).delete()
    db.session.delete(post)
    db.session.commit()
    flash('Пост успешно удален', 'success')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)
import os
import time
from threading import Lock
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
import pymysql
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Flask-Login設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'ログインが必要です。'


# ユーザーモデル
class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

    @staticmethod
    def get_user_by_email(email):
        """メールアドレスでユーザーを取得"""
        try:
            conn = pymysql.connect(**db_params)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, email, password_hash FROM users WHERE email = %s', (email,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user_data:
                return {'id': user_data[0], 'name': user_data[1], 'email': user_data[2], 'password_hash': user_data[3]}
            return None
        except Exception as e:
            print(f"Database error: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id):
        """IDでユーザーを取得"""
        try:
            conn = pymysql.connect(**db_params)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, email FROM users WHERE id = %s', (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user_data:
                return User(user_data[0], user_data[1], user_data[2])
            return None
        except Exception as e:
            print(f"Database error: {e}")
            return None


@login_manager.user_loader
def load_user(user_id):
    """Flask-Loginのユーザー読み込み"""
    return User.get_user_by_id(user_id)


# ログインフォーム
class LoginForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')


# Database connection parameters for MySQL
db_params = {
    'database': os.getenv('MYSQL_DATABASE', 'mysql'),
    'user': os.getenv('MYSQL_USER', 'mysql'),
    'password': os.getenv('MYSQL_PASSWORD', 'mysql'),
    'host': os.getenv('MYSQL_HOST', 'db'),
    'port': int(os.getenv('MYSQL_PORT', '3306'))
}

_test_users_initialized = False
_test_users_lock = Lock()


def create_test_users():
    """テスト用ユーザーを作成（初回起動時のみ）"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**db_params)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]

        if user_count == 0:
            test_users = [
                ('山田太郎', 'yamada@example.com', 'password123'),
                ('佐藤花子', 'sato@example.com', 'password123')
            ]

            for name, email, password in test_users:
                password_hash = generate_password_hash(password)
                cursor.execute(
                    """
                    INSERT INTO users (name, email, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (name, email, password_hash),
                )
                print(f"Created test user: {name} ({email})")

            conn.commit()
            print("Test users created successfully!")

        return True
    except Exception as e:
        print(f"Error creating test users: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def ensure_test_users():
    """テストユーザーが存在するように保証"""
    global _test_users_initialized
    if _test_users_initialized:
        return

    with _test_users_lock:
        if _test_users_initialized:
            return

        for attempt in range(5):
            if create_test_users():
                _test_users_initialized = True
                return
            time.sleep(2)
            print(f"Retrying test user creation (attempt {attempt + 2}/5)")


@app.route('/')
def index():
    ensure_test_users()
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    data = {
        'message': 'Welcome to Flask with MySQL',
        'python_version': '3.11.4',
        'flask_version': '2.3.2',
        'mysql_version': '8.0'
    }
    return render_template('index.html', **data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン処理"""
    ensure_test_users()
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user_data = User.get_user_by_email(form.email.data)
        
        if user_data and check_password_hash(user_data['password_hash'], form.password.data):
            user = User(user_data['id'], user_data['name'], user_data['email'])
            login_user(user)
            flash('ログインに成功しました。', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('メールアドレスまたはパスワードが正しくありません。', 'error')
    
    return render_template('login.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    """ダッシュボード（ログイン後のページ）"""
    return render_template('dashboard.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    """ログアウト処理"""
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # アプリケーション起動時にテストユーザーを作成
    create_test_users()
    app.run(host='0.0.0.0', debug=True)

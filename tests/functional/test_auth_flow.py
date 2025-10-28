"""
認証システムの機能テスト

このモジュールは認証機能全体をテストします。
- ログイン機能
- ログアウト機能
- 認証が必要なページのアクセス制御
- セッション管理
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# アプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app'))

from app import app, User
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    """テスト用のFlaskクライアント"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # CSRFを無効化（テスト用）
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client


class TestLoginFunctionality:
    """ログイン機能のテスト"""
    
    def test_login_page_access(self, client):
        """ログインページへのアクセステスト"""
        response = client.get('/login')
        assert response.status_code == 200
        assert 'ログイン' in response.get_data(as_text=True)
        assert 'メールアドレス' in response.get_data(as_text=True)
        assert 'パスワード' in response.get_data(as_text=True)
    
    @patch('app.User.get_user_by_email')
    def test_login_success(self, mock_get_user, client):
        """ログイン成功テスト"""
        # テストユーザーのモックデータ
        password = "password123"
        password_hash = generate_password_hash(password)
        
        mock_get_user.return_value = {
            'id': 1,
            'name': 'テストユーザー',
            'email': 'test@example.com',
            'password_hash': password_hash
        }
        
        # ログイン試行
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': password
        }, follow_redirects=True)
        
        # アサーション
        assert response.status_code == 200
        assert 'ダッシュボード' in response.get_data(as_text=True)
        assert 'テストユーザー' in response.get_data(as_text=True)
    
    @patch('app.User.get_user_by_email')
    def test_login_invalid_email(self, mock_get_user, client):
        """存在しないメールアドレスでのログインテスト"""
        mock_get_user.return_value = None
        
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert 'メールアドレスまたはパスワードが正しくありません' in response.get_data(as_text=True)
    
    @patch('app.User.get_user_by_email')
    def test_login_invalid_password(self, mock_get_user, client):
        """間違ったパスワードでのログインテスト"""
        password_hash = generate_password_hash("correct_password")
        
        mock_get_user.return_value = {
            'id': 1,
            'name': 'テストユーザー',
            'email': 'test@example.com',
            'password_hash': password_hash
        }
        
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrong_password'
        })
        
        assert response.status_code == 200
        assert 'メールアドレスまたはパスワードが正しくありません' in response.get_data(as_text=True)
    
    def test_login_form_validation(self, client):
        """ログインフォームのバリデーションテスト"""
        # 空のフォーム送信
        response = client.post('/login', data={
            'email': '',
            'password': ''
        })
        
        assert response.status_code == 200
        # バリデーションエラーが表示されることを確認
        response_text = response.get_data(as_text=True)
        assert 'This field is required' in response_text or 'フィールドは必須です' in response_text
    
    def test_login_invalid_email_format(self, client):
        """不正なメールアドレス形式のテスト"""
        response = client.post('/login', data={
            'email': 'invalid_email_format',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert 'Invalid email address' in response_text or 'メールアドレス' in response_text


class TestDashboardAccess:
    """ダッシュボードアクセスのテスト"""
    
    def test_dashboard_requires_login(self, client):
        """ログインしていない状態でダッシュボードアクセステスト"""
        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        # ログインページにリダイレクトされることを確認
        assert 'ログイン' in response.get_data(as_text=True)
    
    @patch('app.User.get_user_by_id')
    @patch('app.User.get_user_by_email')
    def test_dashboard_access_with_login(self, mock_get_by_email, mock_get_by_id, client):
        """ログイン後のダッシュボードアクセステスト"""
        password = "password123"
        password_hash = generate_password_hash(password)
        
        # ログイン用のモック
        mock_get_by_email.return_value = {
            'id': 1,
            'name': 'テストユーザー',
            'email': 'test@example.com',
            'password_hash': password_hash
        }
        
        # セッション維持用のモック
        mock_get_by_id.return_value = User(1, 'テストユーザー', 'test@example.com')
        
        # ログイン
        client.post('/login', data={
            'email': 'test@example.com',
            'password': password
        })
        
        # ダッシュボードアクセス
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert 'ダッシュボード' in response.get_data(as_text=True)
        assert 'テストユーザー' in response.get_data(as_text=True)


class TestLogoutFunctionality:
    """ログアウト機能のテスト"""
    
    @patch('app.User.get_user_by_id')
    @patch('app.User.get_user_by_email')
    def test_logout(self, mock_get_by_email, mock_get_by_id, client):
        """ログアウト機能テスト"""
        password = "password123"
        password_hash = generate_password_hash(password)
        
        # ログイン用のモック
        mock_get_by_email.return_value = {
            'id': 1,
            'name': 'テストユーザー',
            'email': 'test@example.com',
            'password_hash': password_hash
        }
        
        mock_get_by_id.return_value = User(1, 'テストユーザー', 'test@example.com')
        
        # ログイン
        client.post('/login', data={
            'email': 'test@example.com',
            'password': password
        })
        
        # ログアウト
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # ホームページにリダイレクトされることを確認
        response_text = response.get_data(as_text=True)
        assert 'Welcome to Flask with MySQL' in response_text
        
        # ダッシュボードにアクセスできないことを確認
        dashboard_response = client.get('/dashboard', follow_redirects=True)
        assert 'ログイン' in dashboard_response.get_data(as_text=True)


class TestIndexPageBehavior:
    """インデックスページの動作テスト"""
    
    def test_index_page_without_login(self, client):
        """ログインしていない状態でのインデックスページ"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'Welcome to Flask with MySQL' in response.get_data(as_text=True)
        assert 'ログイン' in response.get_data(as_text=True)
    
    @patch('app.User.get_user_by_id')
    @patch('app.User.get_user_by_email')
    def test_index_page_with_login_redirects_to_dashboard(self, mock_get_by_email, mock_get_by_id, client):
        """ログイン済みの場合、インデックスページからダッシュボードにリダイレクト"""
        password = "password123"
        password_hash = generate_password_hash(password)
        
        mock_get_by_email.return_value = {
            'id': 1,
            'name': 'テストユーザー',
            'email': 'test@example.com',
            'password_hash': password_hash
        }
        
        mock_get_by_id.return_value = User(1, 'テストユーザー', 'test@example.com')
        
        # ログイン
        client.post('/login', data={
            'email': 'test@example.com',
            'password': password
        })
        
        # インデックスページアクセス
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert 'ダッシュボード' in response.get_data(as_text=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
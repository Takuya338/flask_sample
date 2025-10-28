"""
認証システムの単体テスト

このモジュールは認証機能の各メソッドをテストします。
- Userクラスのメソッド
- パスワードハッシュ化・検証
- データベース操作
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash, check_password_hash

# アプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app'))

from app import User, app


class TestUser:
    """Userクラスの単体テスト"""
    
    def test_user_initialization(self):
        """ユーザーオブジェクトの初期化テスト"""
        user = User(1, "テストユーザー", "test@example.com")
        assert user.id == 1
        assert user.name == "テストユーザー"
        assert user.email == "test@example.com"
        assert user.is_active is True  # UserMixinのデフォルト
    
    @patch('app.pymysql.connect')
    def test_get_user_by_email_success(self, mock_connect):
        """メールアドレスでのユーザー取得成功テスト"""
        # モックの設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1, "テストユーザー", "test@example.com", "hashed_password")
        
        # テスト実行
        result = User.get_user_by_email("test@example.com")
        
        # アサーション
        assert result is not None
        assert result['id'] == 1
        assert result['name'] == "テストユーザー"
        assert result['email'] == "test@example.com"
        assert result['password_hash'] == "hashed_password"
        
        # データベース呼び出しの確認
        mock_cursor.execute.assert_called_once_with(
            'SELECT id, name, email, password_hash FROM users WHERE email = %s', 
            ("test@example.com",)
        )
    
    @patch('app.pymysql.connect')
    def test_get_user_by_email_not_found(self, mock_connect):
        """メールアドレスでのユーザー取得失敗テスト"""
        # モックの設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        # テスト実行
        result = User.get_user_by_email("nonexistent@example.com")
        
        # アサーション
        assert result is None
    
    @patch('app.pymysql.connect')
    def test_get_user_by_email_database_error(self, mock_connect):
        """データベースエラー時のテスト"""
        # モックの設定（例外を発生させる）
        mock_connect.side_effect = Exception("Database connection failed")
        
        # テスト実行
        result = User.get_user_by_email("test@example.com")
        
        # アサーション
        assert result is None
    
    @patch('app.pymysql.connect')
    def test_get_user_by_id_success(self, mock_connect):
        """IDでのユーザー取得成功テスト"""
        # モックの設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1, "テストユーザー", "test@example.com")
        
        # テスト実行
        result = User.get_user_by_id(1)
        
        # アサーション
        assert result is not None
        assert isinstance(result, User)
        assert result.id == 1
        assert result.name == "テストユーザー"
        assert result.email == "test@example.com"
    
    @patch('app.pymysql.connect')
    def test_get_user_by_id_not_found(self, mock_connect):
        """IDでのユーザー取得失敗テスト"""
        # モックの設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        # テスト実行
        result = User.get_user_by_id(999)
        
        # アサーション
        assert result is None


class TestPasswordSecurity:
    """パスワードセキュリティの単体テスト"""
    
    def test_password_hashing(self):
        """パスワードハッシュ化テスト"""
        password = "test_password123"
        hashed = generate_password_hash(password)
        
        # ハッシュが生成されることを確認
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith('pbkdf2:sha256')
    
    def test_password_verification_success(self):
        """パスワード検証成功テスト"""
        password = "test_password123"
        hashed = generate_password_hash(password)
        
        # 正しいパスワードで検証
        assert check_password_hash(hashed, password) is True
    
    def test_password_verification_failure(self):
        """パスワード検証失敗テスト"""
        password = "test_password123"
        wrong_password = "wrong_password"
        hashed = generate_password_hash(password)
        
        # 間違ったパスワードで検証
        assert check_password_hash(hashed, wrong_password) is False
    
    def test_different_passwords_different_hashes(self):
        """異なるパスワードで異なるハッシュが生成されることをテスト"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = generate_password_hash(password1)
        hash2 = generate_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_salt(self):
        """同じパスワードでも異なるハッシュが生成されることをテスト（ソルト機能）"""
        password = "test_password"
        
        hash1 = generate_password_hash(password)
        hash2 = generate_password_hash(password)
        
        # ソルトにより異なるハッシュが生成される
        assert hash1 != hash2
        
        # どちらも正しく検証される
        assert check_password_hash(hash1, password) is True
        assert check_password_hash(hash2, password) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
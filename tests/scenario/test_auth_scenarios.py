"""
認証システムのシナリオテスト

このモジュールは実際のビジネスシナリオに基づいたテストを実行します。
- 新規ユーザーの一日の利用パターン
- 管理者による複数ユーザーの管理
- 異常なアクセスパターンの検出
- パフォーマンステスト
"""
import pytest
import sys
import os
import time
import concurrent.futures
from unittest.mock import patch, MagicMock

# アプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app'))

from app import app, User
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    """テスト用のFlaskクライアント"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client


class TestNewUserDailyWorkflow:
    """新規ユーザーの一日の利用ワークフロー"""
    
    @patch('app.User.get_user_by_id')
    @patch('app.User.get_user_by_email')
    def test_typical_user_daily_workflow(self, mock_get_by_email, mock_get_by_id, client):
        """典型的なユーザーの一日の利用パターン"""
        
        # テストユーザーの設定
        user_data = {
            'id': 1,
            'name': '田中一郎',
            'email': 'tanaka@company.com',
            'password_hash': generate_password_hash('company123')
        }
        
        mock_get_by_email.return_value = user_data
        mock_get_by_id.return_value = User(user_data['id'], user_data['name'], user_data['email'])
        
        # シナリオ: 朝の出社時ログイン
        print("シナリオ開始: 朝の出社時ログイン")
        
        # 1. ホームページアクセス
        response = client.get('/')
        assert response.status_code == 200
        
        # 2. ログインページアクセス
        response = client.get('/login')
        assert response.status_code == 200
        
        # 3. ログイン実行
        response = client.post('/login', data={
            'email': 'tanaka@company.com',
            'password': 'company123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'ダッシュボード' in response.get_data(as_text=True)
        
        # 4. 日中の複数回ダッシュボードアクセス（業務中の確認）
        for i in range(5):
            response = client.get('/dashboard')
            assert response.status_code == 200
            assert '田中一郎' in response.get_data(as_text=True)
            time.sleep(0.1)  # 短い間隔でのアクセスをシミュレート
        
        # 5. 終業時のログアウト
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert 'Welcome to Flask with MySQL' in response.get_data(as_text=True)
        
        print("シナリオ完了: 正常な一日の業務フロー")
    
    @patch('app.User.get_user_by_id')
    @patch('app.User.get_user_by_email')
    def test_interrupted_workflow_with_session_timeout(self, mock_get_by_email, mock_get_by_id, client):
        """セッションタイムアウトを含む中断されたワークフロー"""
        
        user_data = {
            'id': 2,
            'name': '鈴木次郎',
            'email': 'suzuki@company.com',
            'password_hash': generate_password_hash('secure456')
        }
        
        mock_get_by_email.return_value = user_data
        mock_get_by_id.return_value = User(user_data['id'], user_data['name'], user_data['email'])
        
        # シナリオ: 長時間の離席後の再アクセス
        print("シナリオ開始: 長時間離席後の再アクセス")
        
        # 1. 最初のログイン
        response = client.post('/login', data={
            'email': 'suzuki@company.com',
            'password': 'secure456'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # 2. ダッシュボード確認
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert '鈴木次郎' in response.get_data(as_text=True)
        
        # 3. セッションクリア（長時間離席をシミュレート）
        with client.session_transaction() as sess:
            sess.clear()
        
        # 4. ダッシュボードに再アクセス（ログインが必要になる）
        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert 'ログイン' in response.get_data(as_text=True)
        
        # 5. 再ログイン
        response = client.post('/login', data={
            'email': 'suzuki@company.com',
            'password': 'secure456'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'ダッシュボード' in response.get_data(as_text=True)
        
        print("シナリオ完了: セッションタイムアウト後の再認証")


class TestMultipleUserScenarios:
    """複数ユーザーのシナリオテスト"""
    
    def test_concurrent_user_access(self, client):
        """複数ユーザーの同時アクセス"""
        
        def simulate_user_session(user_email, password, user_name):
            """ユーザーセッションをシミュレート"""
            try:
                with patch('app.User.get_user_by_email') as mock_get_by_email, \
                     patch('app.User.get_user_by_id') as mock_get_by_id:
                    
                    user_data = {
                        'id': hash(user_email) % 1000,  # 簡単なID生成
                        'name': user_name,
                        'email': user_email,
                        'password_hash': generate_password_hash(password)
                    }
                    
                    mock_get_by_email.return_value = user_data
                    mock_get_by_id.return_value = User(user_data['id'], user_data['name'], user_data['email'])
                    
                    # ログイン試行
                    response = client.post('/login', data={
                        'email': user_email,
                        'password': password
                    })
                    
                    return {
                        'user': user_name,
                        'status_code': response.status_code,
                        'success': response.status_code in [200, 302]
                    }
            except Exception as e:
                return {
                    'user': user_name,
                    'status_code': 500,
                    'success': False,
                    'error': str(e)
                }
        
        # 複数ユーザーの同時ログイン試行
        users = [
            ('user1@test.com', 'pass1', 'ユーザー1'),
            ('user2@test.com', 'pass2', 'ユーザー2'),
            ('user3@test.com', 'pass3', 'ユーザー3'),
            ('user4@test.com', 'pass4', 'ユーザー4'),
            ('user5@test.com', 'pass5', 'ユーザー5'),
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(simulate_user_session, email, password, name)
                for email, password, name in users
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 結果の検証
        successful_logins = [r for r in results if r['success']]
        assert len(successful_logins) >= 3, "少なくとも3つのログインが成功する必要があります"
        
        print(f"同時ログインテスト完了: {len(successful_logins)}/{len(users)} 成功")


class TestSecurityScenarios:
    """セキュリティシナリオテスト"""
    
    @patch('app.User.get_user_by_email')
    def test_brute_force_attack_simulation(self, mock_get_user, client):
        """ブルートフォース攻撃のシミュレーション"""
        
        # 正しいユーザーデータを設定
        correct_password = "correct_password"
        user_data = {
            'id': 1,
            'name': 'セキュリティテストユーザー',
            'email': 'security@test.com',
            'password_hash': generate_password_hash(correct_password)
        }
        
        mock_get_user.return_value = user_data
        
        # 間違ったパスワードでの連続試行
        wrong_passwords = [
            '123456', 'password', 'admin', 'qwerty', 'letmein',
            '12345', 'monkey', 'dragon', '111111', 'baseball'
        ]
        
        failed_attempts = 0
        for wrong_password in wrong_passwords:
            response = client.post('/login', data={
                'email': 'security@test.com',
                'password': wrong_password
            })
            
            if response.status_code == 200 and 'メールアドレスまたはパスワードが正しくありません' in response.get_data(as_text=True):
                failed_attempts += 1
        
        # すべての不正な試行が失敗することを確認
        assert failed_attempts == len(wrong_passwords)
        
        # 正しいパスワードでのログインは成功することを確認
        response = client.post('/login', data={
            'email': 'security@test.com',
            'password': correct_password
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'ダッシュボード' in response.get_data(as_text=True)
        
        print("ブルートフォース攻撃シミュレーション完了: すべての不正試行を阻止")
    
    @patch('app.User.get_user_by_email')
    def test_sql_injection_attempt(self, mock_get_user, client):
        """SQLインジェクション攻撃の試行"""
        
        mock_get_user.return_value = None  # ユーザーが見つからない場合をシミュレート
        
        # 典型的なSQLインジェクションペイロード
        malicious_inputs = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin'--",
            "' UNION SELECT * FROM users --",
            "1' OR 1=1#"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post('/login', data={
                'email': malicious_input,
                'password': 'any_password'
            })
            
            # SQLインジェクションが成功していないことを確認
            assert response.status_code == 200
            assert 'ダッシュボード' not in response.get_data(as_text=True)
            
            # エラーメッセージが適切に表示されることを確認
            response_text = response.get_data(as_text=True)
            assert ('メールアドレスまたはパスワードが正しくありません' in response_text or
                    'Invalid email address' in response_text)
        
        print("SQLインジェクション攻撃テスト完了: すべての攻撃を阻止")


class TestPerformanceScenarios:
    """パフォーマンステストシナリオ"""
    
    @patch('app.User.get_user_by_id')
    @patch('app.User.get_user_by_email')
    def test_rapid_successive_requests(self, mock_get_by_email, mock_get_by_id, client):
        """連続高速リクエストのパフォーマンステスト"""
        
        user_data = {
            'id': 1,
            'name': 'パフォーマンステストユーザー',
            'email': 'performance@test.com',
            'password_hash': generate_password_hash('test123')
        }
        
        mock_get_by_email.return_value = user_data
        mock_get_by_id.return_value = User(user_data['id'], user_data['name'], user_data['email'])
        
        # ログイン
        client.post('/login', data={
            'email': 'performance@test.com',
            'password': 'test123'
        })
        
        # 連続リクエストのパフォーマンス測定
        start_time = time.time()
        request_count = 50
        
        successful_requests = 0
        for i in range(request_count):
            response = client.get('/dashboard')
            if response.status_code == 200:
                successful_requests += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_response_time = total_time / request_count
        
        # パフォーマンス基準の確認
        assert successful_requests == request_count, "すべてのリクエストが成功する必要があります"
        assert avg_response_time < 0.5, f"平均応答時間が遅すぎます: {avg_response_time:.3f}秒"
        assert total_time < 10, f"総実行時間が長すぎます: {total_time:.3f}秒"
        
        print(f"パフォーマンステスト完了: {request_count}リクエスト, 平均{avg_response_time:.3f}秒/リクエスト")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
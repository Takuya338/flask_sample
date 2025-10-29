"""
認証システムのE2E（End-to-End）テスト

このモジュールは認証システム全体の完全なワークフローをテストします。
- 実際のブラウザを使用してテスト
- データベースとの統合テスト
- ユーザーの実際の操作フローをシミュレート
"""
import os
import time
import urllib.error
import urllib.request
import json
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def _wait_for_http(url: str, timeout: int = 60, expect_json: bool = False) -> bool:
    """指定されたURLが応答するまで待機"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url) as response:
                if expect_json:
                    json.loads(response.read().decode("utf-8"))
                return True
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            time.sleep(2)
    return False


@pytest.fixture(scope="session")
def settings():
    """テスト設定"""
    return {
        "app_url": os.getenv("APP_URL", "http://app:5000"),
        "selenium_url": os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444/wd/hub"),
    }


@pytest.fixture(scope="session")
def driver(settings):
    """Seleniumドライバー"""
    selenium_status = settings["selenium_url"].split("/wd/hub", 1)[0] + "/status"
    if not _wait_for_http(selenium_status, expect_json=True):
        pytest.skip("Selenium server is not reachable; skipping E2E tests.")

    # アプリが到達可能になるまで待機
    if not _wait_for_http(settings["app_url"]):
        pytest.skip("Flask app is not reachable; skipping E2E tests.")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Remote(
        command_executor=settings["selenium_url"],
        options=options,
    )

    yield driver
    driver.quit()


class TestCompleteAuthenticationFlow:
    """完全な認証フローのE2Eテスト"""
    
    def test_complete_login_logout_flow(self, driver, settings):
        """ログイン〜ダッシュボード表示〜ログアウトの完全フロー"""
        
        # 1. ホームページにアクセス
        driver.get(settings["app_url"])
        
        # ページが読み込まれるまで待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # ホームページの内容を確認
        assert "Flask with MySQL" in driver.page_source
        
        # 2. ログインページに移動
        login_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "ログイン"))
        )
        login_link.click()
        
        # ログインページが表示されることを確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        assert "ログイン" in driver.page_source
        
        # 3. ログイン情報を入力
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        
        email_field.clear()
        email_field.send_keys("yamada@example.com")
        
        password_field.clear()
        password_field.send_keys("password123")
        
        # 4. ログインボタンをクリック
        login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        login_button.click()
        
        # 5. ダッシュボードにリダイレクトされることを確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # ダッシュボードの内容を確認
        assert "ダッシュボード" in driver.page_source
        assert "山田太郎" in driver.page_source
        assert "yamada@example.com" in driver.page_source
        
        # 6. ログアウトボタンをクリック
        logout_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "ログアウト"))
        )
        logout_button.click()
        
        # 7. ホームページにリダイレクトされることを確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        assert "Welcome to Flask with MySQL" in driver.page_source
        
        # 8. ダッシュボードに直接アクセスしてリダイレクトされることを確認
        driver.get(f"{settings['app_url']}/dashboard")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        assert "ログイン" in driver.page_source
    
    def test_invalid_login_attempt(self, driver, settings):
        """無効なログイン試行のテスト"""
        
        # ログインページに移動
        driver.get(f"{settings['app_url']}/login")
        
        # ページが読み込まれるまで待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        # 無効なログイン情報を入力
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        
        email_field.clear()
        email_field.send_keys("invalid@example.com")
        
        password_field.clear()
        password_field.send_keys("wrongpassword")
        
        # ログインボタンをクリック
        login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        login_button.click()
        
        # エラーメッセージが表示されることを確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "flash-error"))
        )
        
        error_message = driver.find_element(By.CLASS_NAME, "flash-error")
        assert "メールアドレスまたはパスワードが正しくありません" in error_message.text
        
        # まだログインページにいることを確認
        assert driver.find_element(By.NAME, "email") is not None
    
    def test_form_validation(self, driver, settings):
        """フォームバリデーションのテスト"""
        
        # ログインページに移動
        driver.get(f"{settings['app_url']}/login")
        
        # ページが読み込まれるまで待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        # 空のフォームで送信
        login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        login_button.click()
        
        # バリデーションエラーが表示されることを確認
        # HTML5のrequiredバリデーションまたはWTFormsのバリデーション
        email_field = driver.find_element(By.NAME, "email")
        assert email_field.get_attribute("required") is not None
        
        password_field = driver.find_element(By.NAME, "password")
        assert password_field.get_attribute("required") is not None


class TestDashboardFeatures:
    """ダッシュボード機能のE2Eテスト"""
    
    def test_dashboard_user_information_display(self, driver, settings):
        """ダッシュボードでのユーザー情報表示テスト"""
        
        # ログインページに移動してログイン
        driver.get(f"{settings['app_url']}/login")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        
        email_field.send_keys("sato@example.com")
        password_field.send_keys("password123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        login_button.click()
        
        # ダッシュボードでユーザー情報を確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "user-info"))
        )
        
        user_info = driver.find_element(By.CLASS_NAME, "user-info")
        assert "佐藤花子" in user_info.text
        assert "sato@example.com" in user_info.text
        
        # 機能リストが表示されることを確認
        feature_list = driver.find_element(By.CLASS_NAME, "feature-list")
        assert "メールアドレスとパスワードでのログイン認証" in feature_list.text
        assert "ユーザー情報の表示" in feature_list.text
    
    def test_dashboard_navigation_links(self, driver, settings):
        """ダッシュボードのナビゲーションリンクテスト"""
        
        # ログイン処理
        driver.get(f"{settings['app_url']}/login")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        driver.find_element(By.NAME, "email").send_keys("yamada@example.com")
        driver.find_element(By.NAME, "password").send_keys("password123")
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        
        # ダッシュボードでリンクを確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "ホームページ"))
        )
        
        # ホームページへのリンク
        home_link = driver.find_element(By.LINK_TEXT, "ホームページ")
        assert home_link.get_attribute("href").endswith("/")


class TestSecurityFeatures:
    """セキュリティ機能のE2Eテスト"""
    
    def test_unauthorized_access_redirect(self, driver, settings):
        """未認証でのダッシュボードアクセステスト"""
        
        # 直接ダッシュボードにアクセス
        driver.get(f"{settings['app_url']}/dashboard")
        
        # ログインページにリダイレクトされることを確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        assert "ログイン" in driver.page_source
        assert driver.current_url.endswith("/login")
    
    def test_session_persistence(self, driver, settings):
        """セッション持続性のテスト"""
        
        # ログイン
        driver.get(f"{settings['app_url']}/login")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        driver.find_element(By.NAME, "email").send_keys("yamada@example.com")
        driver.find_element(By.NAME, "password").send_keys("password123")
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        
        # ダッシュボードに到達
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        assert "ダッシュボード" in driver.page_source
        
        # 別のページに移動してから戻る
        driver.get(settings["app_url"])
        time.sleep(1)
        driver.get(f"{settings['app_url']}/dashboard")
        
        # まだログインしていることを確認
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        assert "ダッシュボード" in driver.page_source
        assert "山田太郎" in driver.page_source


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
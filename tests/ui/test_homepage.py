import json
import os
import time
import urllib.error
import urllib.request

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def _wait_for_http(url: str, timeout: int = 60, expect_json: bool = False) -> bool:
    """Poll the given URL until it responds or the timeout is reached."""
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
    return {
        "app_url": os.getenv("APP_URL", "http://app:5000"),
        "selenium_url": os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444/wd/hub"),
    }


@pytest.fixture(scope="session")
def driver(settings):
    selenium_status = settings["selenium_url"].split("/wd/hub", 1)[0] + "/status"
    if not _wait_for_http(selenium_status, expect_json=True):
        pytest.skip("Selenium server is not reachable; skipping UI tests.")

    # Wait for the app to become reachable before starting the test session.
    if not _wait_for_http(settings["app_url"]):
        pytest.skip("Flask app is not reachable; skipping UI tests.")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,720")
    driver = webdriver.Remote(
        command_executor=settings["selenium_url"],
        options=options,
    )

    yield driver
    driver.quit()


def test_homepage_renders(driver, settings):
    driver.get(settings["app_url"])

    heading = WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h1"))
    )
    assert "Flask with MySQL" in heading.text


def test_db_test_page_status(driver, settings):
    target_url = f"{settings['app_url']}/db-test"

    for attempt in range(5):
        driver.get(target_url)
        try:
            status_banner = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "success"))
            )
            assert "Database connection successful" in status_banner.text
            break
        except TimeoutException:
            time.sleep(3)
    else:
        pytest.fail("Database test page did not report success within the expected time.")


def test_login_page_renders(driver, settings):
    """ログインページの表示テスト"""
    target_url = f"{settings['app_url']}/login"
    driver.get(target_url)

    # ページタイトルの確認
    heading = WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h1"))
    )
    assert "ログイン" in heading.text

    # フォーム要素の存在確認
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    password_field = driver.find_element(By.NAME, "password")
    submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")

    assert email_field is not None
    assert password_field is not None
    assert submit_button is not None

    # テストアカウント情報の表示確認
    assert "yamada@example.com" in driver.page_source
    assert "password123" in driver.page_source


def test_login_functionality(driver, settings):
    """ログイン機能のUIテスト"""
    # ログインページに移動
    driver.get(f"{settings['app_url']}/login")
    
    # フォーム要素の取得
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    password_field = driver.find_element(By.NAME, "password")
    submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")

    # テストアカウントでログイン
    email_field.send_keys("yamada@example.com")
    password_field.send_keys("password123")
    submit_button.click()

    # ダッシュボードにリダイレクトされることを確認
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h1"))
    )
    
    assert "ダッシュボード" in driver.page_source
    assert "山田太郎" in driver.page_source


def test_logout_functionality(driver, settings):
    """ログアウト機能のUIテスト"""
    # まずログイン
    driver.get(f"{settings['app_url']}/login")
    
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    password_field = driver.find_element(By.NAME, "password")
    
    email_field.send_keys("sato@example.com")
    password_field.send_keys("password123")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    
    # ダッシュボードでログアウトボタンをクリック
    logout_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "ログアウト"))
    )
    logout_button.click()
    
    # ホームページにリダイレクトされることを確認
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h1"))
    )
    assert "Welcome to Flask with MySQL" in driver.page_source


def test_navigation_flow(driver, settings):
    """ナビゲーションフローのUIテスト"""
    # ホームページから開始
    driver.get(settings["app_url"])
    
    # ログインボタンをクリック
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "ログイン"))
    )
    login_button.click()
    
    # ログインページに移動したことを確認
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    assert "ログイン" in driver.page_source
    
    # ホームに戻るリンクをクリック
    back_link = driver.find_element(By.LINK_TEXT, "ホームに戻る")
    back_link.click()
    
    # ホームページに戻ることを確認
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.TAG_NAME, "h1"))
    )
    assert "Welcome to Flask with MySQL" in driver.page_source

#!/usr/bin/env python3
"""
データベース初期化時にテストユーザーを作成するスクリプト
"""
import os
import pymysql
from werkzeug.security import generate_password_hash

# データベース接続パラメータ
db_params = {
    'database': os.getenv('MYSQL_DATABASE', 'mysql'),
    'user': os.getenv('MYSQL_USER', 'mysql'),
    'password': os.getenv('MYSQL_PASSWORD', 'mysql'),
    'host': os.getenv('MYSQL_HOST', 'db'),
    'port': int(os.getenv('MYSQL_PORT', '3306'))
}

def create_test_users():
    """テスト用ユーザーを作成"""
    try:
        # データベース接続
        conn = pymysql.connect(**db_params)
        cursor = conn.cursor()
        
        # テストユーザーのデータ
        test_users = [
            ('山田太郎', 'yamada@example.com', 'password123'),
            ('佐藤花子', 'sato@example.com', 'password123')
        ]
        
        for name, email, password in test_users:
            # パスワードハッシュを生成
            password_hash = generate_password_hash(password)
            
            # ユーザーを挿入（既存の場合は無視）
            cursor.execute("""
                INSERT IGNORE INTO users (name, email, password_hash) 
                VALUES (%s, %s, %s)
            """, (name, email, password_hash))
            
            print(f"Created user: {name} ({email})")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Test users created successfully!")
        
    except Exception as e:
        print(f"Error creating test users: {e}")

if __name__ == "__main__":
    create_test_users()
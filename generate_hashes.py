#!/usr/bin/env python3
"""
テスト用ユーザーのパスワードハッシュを生成するスクリプト
"""
from werkzeug.security import generate_password_hash

# テスト用パスワード
password = "password123"

# パスワードハッシュを生成
hash1 = generate_password_hash(password)
hash2 = generate_password_hash(password)

print("Generated password hashes for 'password123':")
print(f"User 1 hash: {hash1}")
print(f"User 2 hash: {hash2}")

# SQL用のINSERT文を生成
print("\nSQL INSERT statements:")
print(f"INSERT IGNORE INTO users (name, email, password_hash) VALUES")
print(f"('山田太郎', 'yamada@example.com', '{hash1}'),")
print(f"('佐藤花子', 'sato@example.com', '{hash2}');")
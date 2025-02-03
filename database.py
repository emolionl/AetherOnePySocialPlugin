import sqlite3
from datetime import datetime
from typing import List

class SocialDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create analysis_keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id INTEGER NOT NULL,
                key TEXT UNIQUE NOT NULL,
                session_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                status TEXT DEFAULT 'active',
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        self.conn.commit()

    def save_user(self, username: str, email: str, token: str = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (username, email, token)
            VALUES (?, ?, ?)
        ''', (username, email, token))
        self.conn.commit()
        return cursor.lastrowid

    def update_user_token(self, email: str, token: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users SET token = ? WHERE email = ?
        ''', (token, email))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_user_by_email(self, email: str) -> dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # Analysis Keys CRUD operations
    def create_analysis_key(self, key_id: int, key: str, analysis_id: int, user_id: int, 
                          expires_at: datetime = None, metadata: str = None) -> int:
        """Create a new analysis key"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO analysis_keys (key_id, key, analysis_id, user_id, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (key_id, key, analysis_id, user_id, expires_at, metadata))
        self.conn.commit()
        return cursor.lastrowid

    def get_analysis_key(self, key: str) -> dict:
        """Get analysis key by key string"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM analysis_keys WHERE key = ?
        ''', (key,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_analysis_key_id(self, key_id: int) -> dict:
        """Get analysis key by key string"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM analysis_keys WHERE key_id = ?
        ''', (key_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_analysis_keys_by_user(self, user_id: int) -> List[dict]:
        """Get all analysis keys for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM analysis_keys 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_analysis_keys_by_analysis(self, analysis_id: int) -> List[dict]:
        """Get all keys for a specific analysis"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM analysis_keys 
            WHERE analysis_id = ? 
            ORDER BY created_at DESC
        ''', (analysis_id,))
        return [dict(row) for row in cursor.fetchall()]

    def update_analysis_key_status(self, key: str, status: str) -> bool:
        """Update analysis key status"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE analysis_keys 
            SET status = ? 
            WHERE key = ?
        ''', (status, key))
        self.conn.commit()
        return cursor.rowcount > 0

    def update_analysis_key_metadata(self, key: str, metadata: str) -> bool:
        """Update analysis key metadata"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE analysis_keys 
            SET metadata = ? 
            WHERE key = ?
        ''', (metadata, key))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_analysis_key(self, key: str) -> bool:
        """Delete an analysis key"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM analysis_keys 
            WHERE key = ?
        ''', (key,))
        self.conn.commit()
        return cursor.rowcount > 0

    def cleanup_expired_keys(self) -> int:
        """Remove expired analysis keys"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM analysis_keys 
            WHERE expires_at IS NOT NULL 
            AND expires_at < CURRENT_TIMESTAMP
        ''')
        self.conn.commit()
        return cursor.rowcount

    def deactivate_analysis_keys(self, analysis_id: int) -> int:
        """Deactivate all keys for an analysis"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE analysis_keys 
            SET status = 'inactive' 
            WHERE analysis_id = ?
        ''', (analysis_id,))
        self.conn.commit()
        return cursor.rowcount

    def close(self):
        self.conn.close() 
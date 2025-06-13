import sqlite3
from datetime import datetime
from typing import List

class SocialDatabase:
    def __init__(self, db_path: str):
        print(f"[DEBUG] Initializing SocialDatabase at {db_path}")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        print("[DEBUG] Creating tables in SocialDatabase if not exist")
        cursor = self.conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_user_id INTEGER NOT NULL,
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

        # Create servers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def save_user(self, username: str, email: str, token: str, server_user_id: int) -> int:
        cursor = self.conn.cursor()
        print(f"[DEBUG] Saving user: {username}, {email}, {token}, {server_user_id}")
        cursor.execute('''
            INSERT OR REPLACE INTO users (username, email, token, server_user_id)
            VALUES (?, ?, ?, ?)
        ''', (username, email, token, server_user_id))
        self.conn.commit()
        print(f"[DEBUG] User saved: {cursor.lastrowid}")
        return cursor.lastrowid

    def update_user_token(self, email: str, token: str) -> bool:
        cursor = self.conn.cursor()
        print(f"[DEBUG] Updating user token: {email}, {token}")
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
    
    def get_only_user(self) -> dict: # only one user allowed in the users table, because there is not need for multiple users
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_user_token(self, email: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute('SELECT token FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        return row['token'] if row else None

    # Analysis Keys CRUD operations
    def create_analysis_key(self, key_id: int, key: str, session_id: int, user_id: int, 
                          expires_at: datetime = None, metadata: str = None) -> int:
        """Create a new analysis key"""
        cursor = self.conn.cursor()
        print(f"key_id: {key_id}, key: {key}, session_id: {session_id}, user_id: {user_id}, expires_at: {expires_at}, metadata: {metadata}")
        cursor.execute('''
            INSERT INTO analysis_keys (key_id, key, session_id, user_id, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (key_id, key, session_id, user_id, expires_at, metadata))
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

    def upsert_user_token(self, username: str, email: str, token: str, server_user_id: int = None) -> bool:
        cursor = self.conn.cursor()
        # Always keep only one user: delete all others
        cursor.execute('DELETE FROM users WHERE email != ?', (email,))
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        if row:
            # User exists, update all fields
            update_fields = 'username = ?, email = ?, token = ?'
            params = [username, email, token]
            if server_user_id is not None:
                update_fields += ', server_user_id = ?'
                params.append(server_user_id)
            cursor.execute(f'UPDATE users SET {update_fields} WHERE id = ?', params + [row['id']])
        else:
            # No user exists, insert new
            cursor.execute('''
                INSERT INTO users (username, email, token{server_id}) VALUES (?, ?, ?{server_id_val})
            '''.format(
                server_id=', server_user_id' if server_user_id is not None else '',
                server_id_val=', ?' if server_user_id is not None else ''
            ), ([username, email, token] + ([server_user_id] if server_user_id is not None else [])))
        self.conn.commit()
        return True

    def add_server(self, url: str, description: str = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO servers (url, description) VALUES (?, ?)
        ''', (url, description))
        self.conn.commit()
        return cursor.lastrowid

    def get_servers(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM servers ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]

    def get_server_by_id(self, server_id: int) -> dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM servers WHERE id = ?', (server_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_server(self, server_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM servers WHERE id = ?', (server_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def list_all_sessions(self):
        """Return all sessions across all cases."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM sessions ORDER BY created DESC')
        rows = cursor.fetchall()
        return [self._row_to_session(row) for row in rows] 
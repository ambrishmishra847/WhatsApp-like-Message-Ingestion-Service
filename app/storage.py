import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

class Database:
    def __init__(self, db_path: str):
        # Handle sqlite://// format if passed
        if db_path.startswith("sqlite:///"):
            self.db_path = db_path.replace("sqlite:///", "")
        else:
            self.db_path = db_path

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def insert_message(self, data: dict) -> str:
        conn = self._get_conn()
        try:
            created_at = datetime.utcnow().isoformat() + "Z"
            conn.execute("""
                INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data['message_id'], data['from'], data['to'], data['ts'], data.get('text'), created_at))
            conn.commit()
            return "created"
        except sqlite3.IntegrityError:
            return "duplicate"
        finally:
            conn.close()

    def get_messages(self, limit: int, offset: int, 
                     from_filter: Optional[str], 
                     since_filter: Optional[str], 
                     q_filter: Optional[str]) -> Tuple[List[dict], int]:
        conn = self._get_conn()
        
        conditions = ["1=1"]
        params = []

        if from_filter:
            conditions.append("from_msisdn = ?")
            params.append(from_filter)
        if since_filter:
            conditions.append("ts >= ?")
            params.append(since_filter)
        if q_filter:
            conditions.append("text LIKE ?")
            params.append(f"%{q_filter}%")

        where_clause = " AND ".join(conditions)

        # Total count for the filter
        count_query = f"SELECT COUNT(*) as count FROM messages WHERE {where_clause}"
        total = conn.execute(count_query, params).fetchone()['count']

        # Paginated results
        fetch_query = f"""
            SELECT * FROM messages 
            WHERE {where_clause} 
            ORDER BY ts ASC, message_id ASC 
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor = conn.execute(fetch_query, params)
        
        results = []
        for row in cursor:
            results.append({
                "message_id": row['message_id'],
                "from": row['from_msisdn'],
                "to": row['to_msisdn'],
                "ts": row['ts'],
                "text": row['text']
            })
            
        conn.close()
        return results, total

    def get_stats(self) -> Dict[str, Any]:
        conn = self._get_conn()
        
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        senders_count = conn.execute("SELECT COUNT(DISTINCT from_msisdn) FROM messages").fetchone()[0]
        
        # Top 10 senders by message count
        cursor = conn.execute("""
            SELECT from_msisdn, COUNT(*) as count 
            FROM messages 
            GROUP BY from_msisdn 
            ORDER BY count DESC 
            LIMIT 10
        """)
        messages_per_sender = [{"from": row['from_msisdn'], "count": row['count']} for row in cursor]
        
        # Range of messages
        range_row = conn.execute("SELECT MIN(ts), MAX(ts) FROM messages").fetchone()
        
        conn.close()
        return {
            "total_messages": total_messages,
            "senders_count": senders_count,
            "messages_per_sender": messages_per_sender,
            "first_message_ts": range_row[0],
            "last_message_ts": range_row[1]
        }
    
    def check_health(self) -> bool:
        try:
            conn = self._get_conn()
            conn.execute("SELECT 1")
            conn.close()
            return True
        except:
            return False

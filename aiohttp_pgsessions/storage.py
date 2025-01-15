import base64
import json
from datetime import datetime, timedelta

from aiohttp_session import AbstractStorage, Session


class PostgresStorage(AbstractStorage):
    def __init__(self, db_con, *, cookie_name="AIOHTTP_SESSION",
                 domain=None, max_age=365*24*60*60, path='/',
                 secure=None, httponly=True, samesite=None):
        super().__init__(cookie_name=cookie_name, domain=domain,
                        max_age=max_age, path=path, secure=secure,
                        httponly=httponly, samesite=samesite)
        self.db_con = db_con

        # ensure table exists and clean old sessions on startup
        #self._create_table_if_not_exists()
        
        self.cleanup()

    # I don't think it's agood idea to give enough right to the client to create a table and index
    # def _create_table_if_not_exists(self):
    #     """Create the sessions table if it doesn't exist"""
    #     with self.db_con.cursor() as cur:
    #         cur.execute("""
    #             CREATE TABLE IF NOT EXISTS sessions (
    #                 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    #                 data bytea NOT NULL,
    #                 created_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
    #                 expires_at timestamp NOT NULL
    #             )
    #         """)
    #         # Create index on expires_at for faster cleanup
    #         cur.execute("""
    #             CREATE INDEX IF NOT EXISTS idx_sessions_expires_at 
    #             ON sessions (expires_at)
    #         """)
    #     self.db_con.commit()

    async def load_session(self, request):
        cookie = self.load_cookie(request)
        if not cookie:
            return Session(None, data=None, new=True, max_age=self.max_age)

        with self.db_con.cursor() as cur:
            cur.execute(
                "SELECT data FROM sessions WHERE id = %s AND expires_at > now()",
                (cookie,)
            )
            result = cur.fetchone()
            if result:
                data = self._decoder(result[0])
                return Session(cookie, data=data, new=False, max_age=self.max_age)

        return Session(None, data=None, new=True, max_age=self.max_age)

    async def save_session(self, request, response, session):
        if session.empty:
            if self.load_cookie(request):
                self.save_cookie(response, "", max_age=0)
            return

        session_id = session.identity
        expires = datetime.now() + timedelta(seconds=self.max_age)
        data_str = self._encoder(self._get_session_data(session))

        with self.db_con.cursor() as cur:
            if not session_id:
                # Let PostgreSQL generate the UUID
                cur.execute("""
                    INSERT INTO sessions (data, expires_at)
                    VALUES (%s, %s)
                    RETURNING id::text
                """, (data_str, expires))
                session_id = cur.fetchone()[0]
                session.set_new_identity(session_id)
            else:
                # Update existing session
                cur.execute("""
                    UPDATE sessions
                    SET data = %s, expires_at = %s
                    WHERE id = %s::uuid
                """, (data_str, expires, session_id))

        self.save_cookie(response, session_id, max_age=self.max_age)

    def cleanup(self):
        """Delete expired sessions"""
        with self.db_con.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE expires_at < now()")

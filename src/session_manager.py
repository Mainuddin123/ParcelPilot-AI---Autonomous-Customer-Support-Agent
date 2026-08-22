import uuid


class SessionManager:

    def __init__(self):
        self.sessions = {}

    def create_session(self):

        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "history": [],
            "pending_escalation": None
        }

        return session_id

    def get_session(
        self,
        session_id
    ):

        if session_id not in self.sessions:

            self.sessions[session_id] = {
                "history": [],
                "pending_escalation": None
            }

        return self.sessions[session_id]

    def add_message(
        self,
        session_id,
        role,
        content
    ):

        session = self.get_session(
            session_id
        )

        session["history"].append({
            "role": role,
            "content": content
        })

    def get_history(
        self,
        session_id
    ):

        session = self.get_session(
            session_id
        )

        return session["history"]

    def clear_session(
        self,
        session_id
    ):

        if session_id in self.sessions:

            del self.sessions[session_id]
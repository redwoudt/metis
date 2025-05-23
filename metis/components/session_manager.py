# SessionManager subsystem
class SessionManager:
    def load_or_create(self, user_id):
        return {"user_id": user_id, "history": []}

    def save(self, user_id, session, prompt, response):
        session["history"].append((prompt, response))

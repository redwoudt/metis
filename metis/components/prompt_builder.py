# PromptBuilder subsystem
class PromptBuilder:
    def build(self, session, user_input):
        return f"[User: {session['user_id']}]\n{user_input}"

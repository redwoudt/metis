# ModelManager subsystem
class Model:
    def generate(self, prompt):
        return f"[MockModel Output]\n{prompt}"

class ModelManager:
    def select(self, session, prompt):
        return Model()

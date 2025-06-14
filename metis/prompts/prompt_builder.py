# prompts/prompt_builder.py

class PromptBuilder:
    """
    Builds structured prompts based on the current state and user input.
    Acts as a bridge between conversational state and prompt formatting logic.
    """

    def __init__(self):
        self.default_tone = "neutral"

    def build_prompt(self, state_name, user_input, preferences=None):
        """
        Construct a prompt using conversation context and user preferences.

        :param state_name: The name of the current conversation state (e.g., 'GreetingState').
        :param user_input: The latest message from the user.
        :param preferences: Optional dict of user preferences (e.g., tone).
        :return: A formatted prompt string.
        """
        tone = preferences.get("tone", self.default_tone) if preferences else self.default_tone

        # Template routing based on state
        if state_name == "GreetingState":
            return f"[Tone: {tone}] Welcome message context: {user_input}"
        elif state_name == "ClarifyingState":
            return f"[Tone: {tone}] Clarify the following: {user_input}"
        elif state_name == "ExecutingState":
            return f"[Tone: {tone}] Execute task: {user_input}"
        elif state_name == "SummarizingState":
            return f"[Tone: {tone}] Provide a summary of: {user_input}"
        else:
            return f"[Tone: {tone}] Default processing for: {user_input}"
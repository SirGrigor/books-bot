class TeachingService:
    def generate_prompt(self, summary):
        """
        Generates a teaching prompt based on the summary.
        """
        return f"Based on the summary: '{summary}', here are some actionable insights you can apply in real life."
import os
import google.generativeai as genai  # Correct import

# Initialize the Gemini client
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

def summarize_with_gemini(text):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"Summarize this: {text}")
        return response.text
    except Exception as e:
        raise RuntimeError(f"Error during summarization: {str(e)}")
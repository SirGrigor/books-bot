# app/services/llm_prompts.py

"""
Collection of prompt templates for advanced LLM processing of book content.
These prompts are designed to work with state-of-the-art models like
Claude 3.7 Sonnet or Gemini for optimal results.
"""

# Chapter detection and analysis prompts
CHAPTER_DETECTION_PROMPT = """
You are an expert literary analyst with the ability to precisely identify chapter 
structures in books. Analyze the provided text and identify clear chapter or section 
boundaries.

For each chapter or major section you identify, provide:
1. The chapter title or number
2. The exact text that marks the beginning of the chapter
3. The exact text that marks the end of the chapter (or indicate if it continues beyond the provided text)

Format your response as a JSON array of objects with the following structure:
[
  {
    "title": "Chapter title or identifier",
    "start_marker": "Text that marks the beginning",
    "end_marker": "Text that marks the end (or empty if it's the end of the provided text)"
  }
]

Text to analyze:
{text_sample}

Only output the JSON array without any additional explanation or commentary.
"""

CHAPTER_SUMMARY_PROMPT = """
You are an expert book summarizer who can distill complex content into clear, insightful summaries.

Summarize the following {chapter_type} {title_context} from the book. 
Focus on:
1. The key ideas and concepts introduced
2. Important insights or arguments presented
3. How this {chapter_type} connects to overall themes in the book (if apparent)
4. Practical applications or takeaways

Make your summary:
- Concise yet comprehensive (3-5 paragraphs)
- Clear and accessible to someone who hasn't read the book
- Engaging and thought-provoking
- Focused on the most valuable and actionable information

{chapter_type} content:
{chapter_text}

Create a summary that would genuinely help someone retain the most important information from this {chapter_type}.
"""

# Quiz and retention prompts
QUIZ_GENERATION_PROMPT = """
You are an expert educator who creates effective learning assessments. 

Based on the following book excerpt, create {num_questions} quiz questions that test 
understanding of the key concepts. For each question, provide the correct answer.

Your questions should:
- Test comprehension of important concepts, not trivial details
- Encourage critical thinking (not just fact recall)
- Be clear and unambiguous
- Vary in difficulty (mix of basic recall and deeper understanding)

Format your response as a JSON array of objects, where each object has 'question' and 'answer' fields:
[
  {
    "question": "What is the main concept the author presents about X?",
    "answer": "The answer explaining the concept clearly."
  }
]

Book excerpt:
{chapter_text}

Only output the JSON array without any additional explanation.
"""

TEACHING_PROMPT_TEMPLATE = """
You are an expert learning coach who understands that teaching a concept is one of the best 
ways to solidify understanding.

Based on the following book excerpt, create a teaching challenge that will help someone 
reinforce their understanding by explaining a key concept to someone else.

The teaching prompt should:
- Focus on one of the most important concepts from the text
- Be specific enough to guide their explanation
- Require synthesizing information (not just regurgitating)
- Be framed as if they were explaining it to someone who has no prior knowledge

Book excerpt:
{chapter_text}

Create a teaching prompt that begins with "Explain the concept of..." or similar phrasing.
Only provide the teaching challenge prompt itself, with no additional text.
"""

# Spaced repetition prompts
RETENTION_REMINDER_PROMPT = """
You are an expert in learning science specializing in spaced repetition and knowledge retention.

This is a {stage_description} spaced repetition reminder about content from the book a user is learning.
The original summary they read was:

{summary}

Create a retention reminder that:
1. Refreshes their memory of key concepts 
2. {stage_specific_instruction}
3. Is concise and engaging (150-200 words)
4. Emphasizes practical applications of the knowledge
5. Includes 1-2 thought-provoking questions that promote active recall

Your reminder should feel like a friendly, helpful message rather than a formal review.
Write in a conversational tone that encourages continued engagement with the material.
"""

# Stage-specific instructions for retention reminders (continued)
STAGE_INSTRUCTIONS = {
	1: "Reinforces the most important points from the original content (1 day after learning)",
	2: "Connects ideas to real-world applications (3 days after learning)",
	3: "Challenges deeper understanding through comparison and analysis (7 days after learning)",
	4: "Provides a comprehensive review linking all major concepts (30 days after learning)"
}

# Application-focused prompts
PRACTICAL_APPLICATION_PROMPT = """
You are an expert at helping people apply theoretical knowledge in practical ways.

Based on the following book excerpt, create 3-5 practical action steps or exercises 
that would help someone implement the key concepts in their daily life.

The action steps should be:
- Specific and actionable
- Realistic for the average person to implement
- Directly connected to the concepts in the text
- Varied in scope (mix of quick wins and deeper practices)
- Designed to build lasting habits or change

Book excerpt:
{chapter_text}

Format your response as a list of action steps with brief explanations of how each 
step relates to the concepts in the text and what benefits it will provide.
"""

CONCEPTUAL_MAPPING_PROMPT = """
You are an expert at identifying and mapping conceptual relationships in complex texts.

Analyze the following book excerpt and create a conceptual map of the key ideas and 
how they relate to each other. Identify:

1. The 5-7 most important concepts presented
2. How these concepts connect to or build upon each other
3. Any hierarchical relationships between concepts
4. Practical implications that emerge from these relationships

Book excerpt:
{chapter_text}

Format your response as a structured outline that shows both the key concepts and 
the relationships between them. Use clear, concise language to describe each concept
and relationship.
"""

# Personalized learning prompts
PERSONALIZATION_PROMPT = """
You are an expert at personalizing learning experiences based on individual interests and goals.

The user is reading "{book_title}" and has indicated interest in applying the concepts to:
{user_interest}

Based on the following excerpt from the book, create personalized insights and suggestions
that connect the book's concepts specifically to the user's stated interest.

Your personalized insights should:
- Make clear connections between book concepts and the user's interest
- Provide practical applications specific to their context
- Highlight aspects of the text most relevant to them
- Offer thoughtful questions for them to consider

Book excerpt:
{chapter_text}

Create 3-5 personalized insights that would be most valuable to this specific user.
"""

# Social learning and discussion prompts
DISCUSSION_QUESTION_PROMPT = """
You are an expert discussion facilitator who knows how to stimulate thoughtful conversation.

Based on the following book excerpt, create 3-5 thought-provoking discussion questions
that would help a group explore and debate the key concepts from the text.

Your questions should:
- Target the most important or controversial ideas
- Encourage multiple perspectives (not have simple right/wrong answers)
- Connect to broader implications or applications
- Promote critical thinking and deeper understanding
- Be engaging and interesting to discuss

Book excerpt:
{chapter_text}

Create discussion questions that would generate meaningful dialogue and deeper learning.
"""

COUNTERARGUMENT_PROMPT = """
You are an expert critical thinker who can analyze ideas from multiple perspectives.

Based on the following excerpt presenting certain viewpoints or arguments, generate 
thoughtful counterarguments or alternative perspectives that challenge or expand upon 
the author's position.

For each major point in the text:
1. Identify the author's key argument or position
2. Present a reasonable counterargument or alternative view
3. Explain the reasoning behind this alternative perspective
4. Suggest how considering both views leads to deeper understanding

Book excerpt:
{chapter_text}

Develop balanced counterarguments that would help someone think more critically about
these ideas without dismissing the value of the original text.
"""

# Retention enhancement prompts
ANALOGY_GENERATION_PROMPT = """
You are an expert at creating powerful analogies that make complex concepts memorable.

Based on the following book excerpt, create 2-3 clear analogies that would help someone
better understand and remember the main concepts.

Your analogies should:
- Compare the book concepts to familiar everyday situations or objects
- Highlight the most important aspects of the concept
- Be simple enough to be easily understood and remembered
- Be vivid and engaging
- Help clarify rather than confuse

Book excerpt:
{chapter_text}

Create memorable analogies that would genuinely help someone retain these concepts.
"""

VISUAL_DESCRIPTION_PROMPT = """
You are an expert at converting abstract concepts into vivid mental imagery.

Based on the following book excerpt, create descriptions of visual representations
that would help someone mentally visualize and remember the key concepts.

Your visual descriptions should:
- Transform abstract ideas into concrete visual imagery
- Use spatial relationships to show connections between concepts
- Incorporate memorable symbols, colors, or scenes
- Create a cohesive visual narrative
- Be detailed enough to create a clear mental image

Book excerpt:
{chapter_text}

Describe visual representations that would make these concepts more concrete and memorable.
"""

def get_chapter_detection_prompt(text_sample):
	"""Returns a formatted chapter detection prompt with the text sample inserted"""
	return CHAPTER_DETECTION_PROMPT.format(text_sample=text_sample[:10000])

def get_chapter_summary_prompt(chapter_text, chapter_title=""):
	"""Returns a formatted chapter summary prompt"""
	chapter_type = "chapter" if chapter_title else "section"
	title_context = f"titled '{chapter_title}'" if chapter_title else ""

	return CHAPTER_SUMMARY_PROMPT.format(
		chapter_type=chapter_type,
		title_context=title_context,
		chapter_text=chapter_text[:8000]
	)

def get_quiz_generation_prompt(chapter_text, num_questions=3):
	"""Returns a formatted quiz generation prompt"""
	return QUIZ_GENERATION_PROMPT.format(
		num_questions=num_questions,
		chapter_text=chapter_text[:8000]
	)

def get_teaching_prompt(chapter_text):
	"""Returns a formatted teaching prompt"""
	return TEACHING_PROMPT_TEMPLATE.format(chapter_text=chapter_text[:8000])

def get_retention_reminder_prompt(summary, stage):
	"""Returns a formatted retention reminder prompt based on the spaced repetition stage"""
	stage_descriptions = {
		1: "first (day 1)",
		2: "second (day 3)",
		3: "third (day 7)",
		4: "fourth (day 30)"
	}

	stage_description = stage_descriptions.get(stage, "spaced repetition")
	stage_specific_instruction = STAGE_INSTRUCTIONS.get(stage, "Reinforces key concepts")

	return RETENTION_REMINDER_PROMPT.format(
		stage_description=stage_description,
		summary=summary[:1500],
		stage_specific_instruction=stage_specific_instruction
	)

def get_practical_application_prompt(chapter_text):
	"""Returns a formatted practical application prompt"""
	return PRACTICAL_APPLICATION_PROMPT.format(chapter_text=chapter_text[:8000])

def get_personalization_prompt(chapter_text, book_title, user_interest):
	"""Returns a formatted personalization prompt"""
	return PERSONALIZATION_PROMPT.format(
		book_title=book_title,
		user_interest=user_interest,
		chapter_text=chapter_text[:8000]
	)

def get_discussion_question_prompt(chapter_text):
	"""Returns a formatted discussion question prompt"""
	return DISCUSSION_QUESTION_PROMPT.format(chapter_text=chapter_text[:8000])

def get_analogy_generation_prompt(chapter_text):
	"""Returns a formatted analogy generation prompt"""
	return ANALOGY_GENERATION_PROMPT.format(chapter_text=chapter_text[:8000])
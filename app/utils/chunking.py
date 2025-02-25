import re
from typing import List, Dict, Optional
import logging
from constants.constants import CHUNKING_SIZE

def split_into_chunks(text: str, chunk_size: int = CHUNKING_SIZE) -> List[str]:
	"""
	Splits text into chunks of specified size, trying to break at paragraph boundaries.

	Args:
		text: The text to be split
		chunk_size: Maximum size of each chunk

	Returns:
		List of text chunks
	"""
	if not text:
		return []

	if len(text) <= chunk_size:
		return [text]

	# Look for paragraph breaks (double newlines)
	paragraph_pattern = r'\n\s*\n'

	chunks = []
	start_pos = 0

	while start_pos < len(text):
		# If remainder is smaller than chunk_size, add it and finish
		if len(text) - start_pos <= chunk_size:
			chunks.append(text[start_pos:])
			break

		# Try to find a paragraph break near the chunk boundary
		# Look for a break in the latter half of the allowed chunk size
		search_start = start_pos + int(chunk_size * 0.5)
		search_end = start_pos + chunk_size

		# Find all paragraph breaks in the search range
		matches = list(re.finditer(paragraph_pattern, text[search_start:search_end]))

		if matches:
			# Use the last paragraph break in the range
			last_match = matches[-1]
			end_pos = search_start + last_match.start() + 1
		else:
			# If no paragraph break found, try to break at a sentence
			sentence_break = find_sentence_break(text, start_pos + chunk_size)
			if sentence_break:
				end_pos = sentence_break
			else:
				# Last resort: break at the chunk size
				end_pos = start_pos + chunk_size

		# Add the chunk
		chunks.append(text[start_pos:end_pos])
		start_pos = end_pos

	logging.info(f"Split text into {len(chunks)} chunks of approximately {chunk_size} characters each")
	return chunks

def find_sentence_break(text: str, target_pos: int) -> Optional[int]:
	"""
	Finds the nearest sentence break before the target position.

	Args:
		text: The text to search in
		target_pos: The target position to find a break before

	Returns:
		Position of the nearest sentence break, or None if not found
	"""
	# Ensure target_pos is within the text
	if target_pos >= len(text):
		target_pos = len(text) - 1

	# Look back up to 200 characters for a sentence end
	search_start = max(0, target_pos - 200)
	search_text = text[search_start:target_pos]

	# Find all sentence ends (., !, ?)
	sentence_ends = []
	for match in re.finditer(r'[.!?]\s', search_text):
		sentence_ends.append(search_start + match.end())

	if sentence_ends:
		return max(sentence_ends)  # Return the last sentence end found
	return None

def split_by_chapters(text: str, chapter_markers: List[Dict]) -> List[Dict]:
	"""
	Splits text by chapter markers.

	Args:
		text: The full text content
		chapter_markers: List of dicts with 'title', 'start_pos', and 'end_pos'

	Returns:
		List of dictionaries with chapter information
	"""
	chapters = []

	for marker in chapter_markers:
		start_pos = marker['start_pos']
		end_pos = marker['end_pos']

		# Ensure positions are within text bounds
		start_pos = max(0, min(start_pos, len(text)))
		end_pos = max(start_pos, min(end_pos, len(text)))

		chapter_content = text[start_pos:end_pos]

		chapters.append({
			'title': marker['title'],
			'content': chapter_content,
			'start_pos': start_pos,
			'end_pos': end_pos
		})

	# Check if there are any gaps and fill them
	chapters = sorted(chapters, key=lambda x: x['start_pos'])
	filled_chapters = []
	last_end = 0

	for chapter in chapters:
		# If there's a gap, create a chapter for it
		if chapter['start_pos'] > last_end:
			gap_content = text[last_end:chapter['start_pos']]
			if len(gap_content.strip()) > 100:  # Only add if gap has substantial content
				filled_chapters.append({
					'title': 'Untitled Section',
					'content': gap_content,
					'start_pos': last_end,
					'end_pos': chapter['start_pos']
				})

		filled_chapters.append(chapter)
		last_end = chapter['end_pos']

	# If there's content after the last chapter, add it
	if last_end < len(text):
		remaining = text[last_end:]
		if len(remaining.strip()) > 100:
			filled_chapters.append({
				'title': 'Closing Section',
				'content': remaining,
				'start_pos': last_end,
				'end_pos': len(text)
			})

	logging.info(f"Split text into {len(filled_chapters)} chapters")
	return filled_chapters

def extract_semantic_chunks(text: str, max_chunk_size: int = CHUNKING_SIZE) -> List[str]:
	"""
	Extracts semantic chunks from text based on content similarity and sections.
	Uses sentence and paragraph breaks to maintain context integrity.

	Args:
		text: The text to analyze
		max_chunk_size: Maximum size for any single chunk

	Returns:
		List of semantic text chunks
	"""
	# Look for potential section headers
	section_header_pattern = r'(?:\n|\r\n|\r)(?:[A-Z][A-Za-z\s]+:|\d+\.\s+[A-Z]|\*\*[^*]+\*\*|\b[A-Z][A-Z\s]+\b)'
	potential_headers = list(re.finditer(section_header_pattern, text))

	if len(potential_headers) > 3:
		# If we found likely section headers, use them as chunk boundaries
		chunks = []
		last_pos = 0

		for match in potential_headers:
			header_pos = match.start()

			# Skip headers that are too close together
			if header_pos - last_pos < 500:
				continue

			# If the chunk would be too large, do paragraph-based splitting instead
			if header_pos - last_pos > max_chunk_size:
				sub_chunks = split_into_chunks(text[last_pos:header_pos], max_chunk_size)
				chunks.extend(sub_chunks)
			else:
				chunks.append(text[last_pos:header_pos])

			last_pos = header_pos

		# Add the final chunk
		if last_pos < len(text):
			remaining_text = text[last_pos:]
			if len(remaining_text) > max_chunk_size:
				sub_chunks = split_into_chunks(remaining_text, max_chunk_size)
				chunks.extend(sub_chunks)
			else:
				chunks.append(remaining_text)

		logging.info(f"Split text into {len(chunks)} semantic chunks based on section headers")
		return chunks
	else:
		# Fall back to paragraph-based chunking
		return split_into_chunks(text, max_chunk_size)
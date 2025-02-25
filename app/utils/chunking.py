def split_into_chunks(text, chunk_size=1000):
	return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def split_into_chunks(text, chunk_size=1000):
	"""
	Splits text into chunks of specified size.
	"""
	return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
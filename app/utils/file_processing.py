# app/utils/file_processing.py
from PyPDF2 import PdfReader
from ebooklib import epub
from lxml import etree

def extract_text_from_pdf(file_path):
	reader = PdfReader(file_path)
	full_text = ""
	for page in reader.pages:
		full_text += page.extract_text()
	return full_text

def extract_text_from_epub(file_path):
	book = epub.read_epub(file_path)
	full_text = ""
	for item in book.get_items():
		if item.get_type() == ebooklib.ITEM_DOCUMENT:
			full_text += item.get_content().decode('utf-8')
	return full_text

def extract_text_from_fb2(file_path):
	tree = etree.parse(file_path)
	full_text = "".join(tree.xpath("//body//text()"))
	return full_text
import pdfplumber
import fitz
import os
import zipfile
import re
import logging
import warnings
import sys
import contextlib
import pymupdf4llm
import pathlib
from pdf_download import output_folder

directory = rf"C:\Users\navan\Downloads\Data Extraction\{output_folder}"
print(directory)

pdfs = os.listdir(directory)

def remove_content_before_abstract(text):
    match = re.search(r'\babstract\b', text, re.IGNORECASE)
    if match:
        return text[match.start():]  
    return text  


for pdf in pdfs:
    pdf_path = os.path.join(directory, pdf)
    base_output_dir = os.path.join(directory, os.path.splitext(pdf)[0])
    zip_file_path = os.path.join(directory, f'{os.path.splitext(pdf)[0]}.zip')

    os.makedirs(base_output_dir, exist_ok=True)

    pdf_document = fitz.open(pdf_path)
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        image_list = page.get_images(full=True)

        for image_index, image in enumerate(image_list):
            xref = image[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_filename = os.path.join(base_output_dir, f"page_{page_number + 1}_image_{image_index + 1}.png")

            with open(image_filename, "wb") as image_file:
                image_file.write(image_bytes)

    pdf_document.close()
    
    filename = os.path.basename(pdf_path)
    base_filename = os.path.splitext(filename)[0]
    
    outname_md = os.path.join(base_output_dir, f"{base_filename}.md")
    md_text = pymupdf4llm.to_markdown(pdf_path)

    #md_text = remove_content_before_abstract(md_text)
    
    pathlib.Path(outname_md).write_bytes(md_text.encode())

    outname_txt = os.path.join(base_output_dir, f"{base_filename}.txt")
    pathlib.Path(outname_txt).write_bytes(md_text.encode()) 

    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for root, dirs, files in os.walk(base_output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, base_output_dir))

print("Extraction, filtering, and ZIP creation completed.")

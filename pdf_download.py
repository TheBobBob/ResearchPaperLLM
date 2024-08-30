import json
import os
import paperscraper

from query import final_query_set_name
from paperscraper.pdf import save_pdf

from paperscraper.pdf import save_pdf_from_dump

output_folder = f'pdfs_{final_query_set_name}'
os.makedirs(output_folder, exist_ok=True)

save_pdf_from_dump(final_query_set_name, pdf_path=output_folder, key_to_save='doi')
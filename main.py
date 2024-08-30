import os
import re
import zipfile
import pathlib
import pdfplumber
import fitz
import logging
import warnings
import sys
import contextlib
import ollama
import pymupdf4llm
from paperscraper.arxiv import get_and_dump_arxiv_papers
from paperscraper.pdf import save_pdf_from_dump


class PaperProcessor:
    def __init__(self, query_sets, max_results=1):
        self.query_sets = query_sets
        self.max_results = max_results
        self.query = query_sets[:3]
        self.output_folder = None

    def process_queries(self):
        var1 = self.query_sets[0]
        get_and_dump_arxiv_papers(self.query, output_filepath=f'{var1}.jsonl', max_results=self.max_results)
        final_query_set_name = f'{var1}.jsonl'
        self.output_folder = f'pdfs_{final_query_set_name}'
        print(final_query_set_name)

        os.makedirs(self.output_folder, exist_ok=True)
        save_pdf_from_dump(final_query_set_name, pdf_path=self.output_folder, key_to_save='doi')

        return self.output_folder

class PDFExtractor:
    def __init__(self, directory):
        self.directory = directory
        self.pdfs = os.listdir(directory)

    def extract_images_and_text(self):
        for pdf in self.pdfs:
            pdf_path = os.path.join(self.directory, pdf)
            base_output_dir = os.path.join(self.directory, os.path.splitext(pdf)[0])
            zip_file_path = os.path.join(self.directory, f'{os.path.splitext(pdf)[0]}.zip')

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
            pathlib.Path(outname_md).write_bytes(md_text.encode())

            outname_txt = os.path.join(base_output_dir, f"{base_filename}.txt")
            pathlib.Path(outname_txt).write_bytes(md_text.encode())

            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for root, dirs, files in os.walk(base_output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, base_output_dir))

        print("Extraction, filtering, and ZIP creation completed.")

class MarkdownProcessor:
    categories = ['abstract', 'methods', 'methodology', 'discussion', 'references', 'conclusion', 'introduction', 'methodologies', 'results']

    def __init__(self, directory):
        self.directory = directory

    @staticmethod
    def split_markdown_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        sections = []
        current_section = []

        for line in content.splitlines():
            if line.startswith(('**', '##', '#', '*')):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
                current_section.append(line)
            else:
                if current_section or line.strip():
                    current_section.append(line)

        if current_section:
            sections.append('\n'.join(current_section))

        return sections

    def process_files(self):
        for subfolder in os.listdir(self.directory):
            subfolder_path = os.path.join(self.directory, subfolder)
            if os.path.isdir(subfolder_path):
                print(f"Found directory: {subfolder_path}")

                for file_name in os.listdir(subfolder_path):
                    if file_name.endswith('.md'):
                        file_path = os.path.join(subfolder_path, file_name)
                        print(f"Found Markdown file: {file_path}")

                        sections = self.split_markdown_file(file_path)
                        organized_sections = self.organize_sections(sections)

                        self.summarize_sections(
                            subfolder_path, sections, file_name,
                            organized_sections['summary'],
                            organized_sections['background_significance'],
                            organized_sections['methods'],
                            organized_sections['results'],
                            organized_sections['discussion'],
                            organized_sections['references']
                        )

    def organize_sections(self, sections):
        category_sections = {}
        combined_text_for_test = ""

        for section in sections:
            text = section.splitlines()
            title = text[0]

            for category in self.categories:
                if category in title.lower():
                    category_sections[category] = section

        methods2 = category_sections.get('methods') or ''
        methodology = category_sections.get('methodology') or ''
        methodologies = category_sections.get('methodologies') or ''

        intro_index = next((i for i, sec in enumerate(sections) if 'introduction' in sec.lower()), None)
        results_index = next((i for i, sec in enumerate(sections) if 'results' in sec.lower()), None)

        methods = ''
        if intro_index is not None and results_index is not None: #make sure this wasnt lost in translation!!
            methods = "\n".join(sections[intro_index + 1:results_index])

        for section in category_sections.values():
            combined_text_for_test += section + "\n"

        abstract = category_sections.get('abstract') or ''
        introduction = category_sections.get('introduction') or ''
        conclusion = category_sections.get('conclusion') or ''
        results2 = category_sections.get('results') or ''
        discussion2 = category_sections.get('discussion') or ''
        references2 = category_sections.get('references') or ''

        # Convert lists to strings before concatenation
        summary = "\n\n\n".join(
            [ "\n".join(abstract) ] + [ introduction ] + [ conclusion ]
        )
        background_significance = introduction + '\n\n\n'
        methods += methods2 or methodology or methodologies + '\n\n\n'
        results = results2
        discussion = discussion2
        
        #split references
        lines = references2.splitlines()
        formatted_references = ""
        current_reference = ""
        for line in lines:
            if line.strip().startswith(tuple([str(i) + "." for i in range(1, 1000)])):
                if current_reference:
                    formatted_references += current_reference.strip() + "\n\n"
                current_reference = line
            else:
                current_reference += "\n" + line
        if current_reference:
            formatted_references += current_reference.strip()
        
        references = formatted_references

        return {
            'summary': summary,
            'background_significance': background_significance,
            'methods': methods,
            'results': results,
            'discussion': discussion,
            'references': references
        }
    def generate_llm_summary(self, model, prompt):
        try:
            
            response = ollama.generate(
                model=model,
                prompt=prompt,
            )
            return response['response']
        except Exception as e:
            print(f"Error generating summary: {e}")
            return ""


    def summarize_sections(self, subfolder_path, sections, file_name, summary, background_significance, methods, results, discussion, references):
    # Extracting title and author sections
        title1 = sections[0:5]
        author = sections[1:4]
        
        # Join lists into single strings
        title1 = '\n'.join(title1) if isinstance(title1, list) else title1
        author = '\n'.join(author) if isinstance(author, list) else author
        summary = '\n'.join(summary) if isinstance(summary, list) else summary
        background_significance = '\n'.join(background_significance) if isinstance(background_significance, list) else background_significance
        methods = '\n'.join(methods) if isinstance(methods, list) else methods
        results = '\n'.join(results) if isinstance(results, list) else results
        discussion = '\n'.join(discussion) if isinstance(discussion, list) else discussion
        references = '\n'.join(references) if isinstance(references, list) else references
        
        # Concatenate sections
        organized_sections = (title1 + '\n\n\n' + 
                            author + '\n\n\n' + 
                            summary + '\n\n\n' + 
                            background_significance + '\n\n\n' + 
                            methods + '\n\n\n' + 
                            results + '\n\n\n' + 
                            discussion + '\n\n\n' + 
                            references)
        
        # Write to file
        with open(os.path.join(subfolder_path, "before.txt"), 'w', encoding='utf-8') as file:
            file.write(organized_sections)
        
        print(f"Summarization complete for {file_name}. Output saved to {os.path.join(subfolder_path, 'before.txt')}")


        title_prompt = f"Context: {title1}  Set the title for the section as '#Title' Directly state the title of the paper. DISREGARD ALL OTHER TEXT."
        author_prompt = f"Context{author}   Set the title for the section as '#Author' State the names of the authors with their affiliations ONLY. DISREGARD ALL OTHER INFORMATION."
        summary_prompt = f"""Context:{summary}  
                            Set the title for the section as '#Summary' 
                            You are a summarizing AI. Summarize the above input in a succinct way, explaining all mathematical functions and defining all terms.
                            There is no limit to the number of words you can use.
                            Do not include the final paragraph of the conclusion.
                            Do not output anything you do not know for certain."""
        background_significance_prompt = f"""Context:{background_significance}
                                            Set the title for the section as '#Background and Significance'
                                            Summarize the provided text.
                                            You are a summarizing AI.
                                            Summarize the above input in a succinct way, being as specific as possible.
                                            There is no limit to the number of words you can use.
                                            Do not output anything you do not know for certain."""
        methods_prompt = f"""Context:{methods}
                            Set the title for the section as '#Methods'
                            Summarize the provided text.
                            You are a summarizing AI.
                            Summarize the provided text in a succinct way, be as specific as possible.
                            Provide the steps outlined in the text in a list format.
                            There is no limit to the number of words you can use.
                            Do not output anything you do not know for certain.
                            
                            Certain types of papers to look out for:
                            1. If it is a modeling type of paper, make sure to include model assumptions and parameters. Do not include values you do not know.
                            2. If it is a genetics type of paper, make sure to include details about genetic variants studied and their potential functional impacts.
                            3. If it is a cell biology type of paper, make sure to include information on cell lines used and specific experimental conditions.
                            4. If it is a molecular biology type of paper, make sure to include the techniques used for gene expression analysis and any relevant controls.
                            5. If it is an ecology type of paper, make sure to include a description of the ecosystems studied and the methods for sampling biodiversity.
                            6. If it is a biochemistry type of paper, make sure to include the types of biochemical assays performed and the key enzymes or metabolites analyzed.
                            7. If it is a pharmacology type of paper, make sure to include the drug targets investigated and the methods used for assessing drug efficacy.
                            8. If it is a physiology type of paper, make sure to include the physiological parameters measured and the conditions under which measurements were taken.
                            9. If it is a biotechnology type of paper, make sure to include the technologies or techniques developed and their potential applications.
                            10. If it is an evolutionary biology type of paper, make sure to include the evolutionary hypotheses tested and the methods used for phylogenetic analysis.
                            11. If it is a computational biology type of paper, make sure to include the algorithms or models used and the types of data inputs and outputs analyzed."""
        results_prompt = f"""Context:{results}
                            Set the title for the section as '#Results'
                            Summarize the provided text.
                            You are a summarizing AI.
                            Summarize the provided text in a succinct way, be as specific as possible.
                            Provide the key findings of the section in a bulleted list, along with the general summary.
                            There is no limit to the number of words you can use.
                            Do not output anything you do not know for certain."""
        discussion_prompt = f"""Context:{discussion}
                            Set the title for the section as '#Discussion'
                            Summarize the provided text.
                            You are a summarizing AI.
                            Summarize the provided text in a succinct way, be as specific as possible.
                            Provide the key points in a bulleted list along with the general summary.
                            There is no limit to the number of words you can use.
                            Do not output anything you do not know for certain."""
        references_prompt = f"""Context:{references}
                            Extract and list only the titles of each paper from the given list of references. 
                            Please ensure that each title is listed one per line and that only the titles are included — ignore authors, journal names, and publication dates. 
                            Include every reference.
                            Do not output anything you do not know for certain.
            
                            List of references:
                            
                            """

        title_llm = self.generate_llm_summary("mistral:7b", title_prompt)
        author_llm = self.generate_llm_summary("mistral:7b", author_prompt)
        summary_llm = self.generate_llm_summary("mistral", summary_prompt)
        background_significance_llm = self.generate_llm_summary("mistral:7b", background_significance_prompt)
        methods_llm = self.generate_llm_summary("mistral:7b", methods_prompt)
        results_llm = self.generate_llm_summary("mistral:7b", results_prompt)
        discussion_llm = self.generate_llm_summary("mistral:7b", discussion_prompt)
        references_llm = self.generate_llm_summary("mistral:7b", references_prompt)

        all_text = "\n\n\n\n\n\n#".join([
            title_llm, author_llm, summary_llm,
            background_significance_llm, methods_llm,
            results_llm, discussion_llm, references_llm
        ])

        output_file_path = os.path.join(subfolder_path, f"{os.path.splitext(file_name)[0]}_summary.txt")

        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(all_text)

        print(f"Summarization complete for {file_name}. Output saved to {output_file_path}")

def main():
    query_sets = ['glioblastoma']  # Example queries
    processor = PaperProcessor(query_sets)
    output_folder = processor.process_queries()

    if output_folder:
        extractor = PDFExtractor(output_folder)
        extractor.extract_images_and_text()

        markdown_processor = MarkdownProcessor(output_folder)
        markdown_processor.process_files()

if __name__ == "__main__":
    main()

"""
what to do:
1. specialize prompts to the papers (see 4)
2. tell it to not hallucinate
3. specialize prompts to biology-related papers
4. if it is a modeling type of paper, be sure to summarize assumption values + parameters. If you do not know the values, do not include values you do not know.

"""
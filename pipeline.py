import os
import zipfile
import pathlib
import pymupdf
import fitz
import ollama
import pymupdf4llm

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

        # Categorize sections based on titles
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
        discussion_index = next((i for i, sec in enumerate(sections) if 'discussion' in sec.lower()), None)

        # Define methods and results sections
        methods = ''
        results = ''
        if intro_index is not None:
            if results_index is not None:
                methods = "\n".join(sections[intro_index + 1:results_index])
                results = sections[results_index]
            elif discussion_index is not None:
                methods = "\n".join(sections[intro_index + 1:discussion_index])
                results = "\n".join(sections[results_index:discussion_index])
            else:
                methods = "\n".join(sections[intro_index + 1:])
        else:
            methods = methods2 or methodology or methodologies

        # Combine all sections
        for section in category_sections.values():
            combined_text_for_test += section + "\n"

        abstract = category_sections.get('abstract') or ''
        introduction = category_sections.get('introduction') or ''
        conclusion = category_sections.get('conclusion') or ''
        discussion2 = category_sections.get('discussion') or ''
        references2 = category_sections.get('references') or ''

        # Format references
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

        # Return organized sections
        return {
            'summary': "\n\n\n".join([abstract, introduction, conclusion]),
            'background_significance': introduction + '\n\n\n',
            'methods': methods + '\n\n\n',
            'results': results,
            'discussion': discussion2,
            'references': references
        }

    def generate_llm_summary(self, model, prompt):
        try:
            response = ollama.generate(
                model=model,
                prompt=prompt
            )
            return response['response']
        except Exception as e:
            print(f"Error generating summary: {e}")
            return ""

    def summarize_sections(self, subfolder_path, sections, file_name, summary, background_significance, methods, results, discussion, references):
        if isinstance(sections, str):
            sections = sections.split('\n\n\n')

        # Extract title and author
        title1 = '\n'.join(sections[:5])
        author = '\n'.join(sections[1:4])
        
        title1 = '\n'.join(title1) if isinstance(title1, list) else title1
        author = '\n'.join(author) if isinstance(author, list) else author
        summary = '\n'.join(summary) if isinstance(summary, list) else summary
        background_significance = '\n'.join(background_significance) if isinstance(background_significance, list) else background_significance
        methods = '\n'.join(methods) if isinstance(methods, list) else methods
        results = '\n'.join(results) if isinstance(results, list) else results
        discussion = '\n'.join(discussion) if isinstance(discussion, list) else discussion
        references = '\n'.join(references) if isinstance(references, list) else references
        
        import re
        pattern = r"\d+\.\s.+?doi:\S+"
        references1 = re.findall(pattern, references, re.DOTALL)
        references2 = "\n\n".join(references1)
        references = re.sub(r"(\n-----\s+)", "\n", references2)

        organized_sections = (title1 + '\n\n\n' + 
                            author + '\n\n\n' + 
                            summary + '\n\n\n' + 
                            background_significance + '\n\n\n' + 
                            methods + '\n\n\n' + 
                            results + '\n\n\n' + 
                            discussion + '\n\n\n' + 
                            references)
        
        with open(os.path.join(subfolder_path, "before.txt"), 'w', encoding='utf-8') as file:
            file.write(organized_sections)
        
        print(f"Segmentation complete for {file_name}. Output saved to {os.path.join(subfolder_path, 'before.txt')}")


        title_prompt = f"Context: {title1}  Set the title for the section as '#Title' Directly state the title of the paper. Disregard all other text."
        author_prompt = f"Context{author}   Set the title for the section as '#Author' State the names of the authors with their affiliations ONLY. Disregard all other information."
        summary_prompt = f"""Context:{summary}
                            Set the title for the section as '#Summary'. Do not include anything like "here is the summary".
                            
                            __
                            You are a summarizing AI tasked with summarizing key sections of a research paper. Please summarize the abstract, introduction, and conclusion into a single concise paragraph. 
                            Focus on capturing the main objectives, methods, key findings, and conclusions from the abstract; the background, research question, and significance from the introduction;
                            and the key results, implications, and future directions from the conclusion. 
                            Ensure the summary is clear, specific, and informative without including unnecessary details.
                            __
                            
                            Do not output anything you do not know for certain.
                            """
        background_significance_prompt = f"""Context:{background_significance}
                                            Set the title for the section as '#Background and Significance'
                                            
                                            __
                                            You are a summarizing AI. Please summarize the provided introduction focusing on the background and significance of the study. 
                                            Highlight the context, the research problem, key literature, and the importance of the study. Ensure the summary captures the rationale behind the research
                                            and its potential impact or contribution to the field, presented as a clean and concise background and significance section.
                                            __
                                            
                                            Do not output anything you do not know for certain."""
        methods_prompt = f"""Context:{methods}
                            Set the title for the section as '#Methods'
                            
                            __
                            You are a summarizing AI. Please summarize the methods section (the provided section), focusing on the experimental design, procedures, materials, and techniques used in the study. 
                            Ensure the summary captures the key steps, methodologies, and any relevant parameters or controls, presented as a clear and concise methods section.
                            Output everything in a bulletpoint format.
                            __
                            
                            Do not output anything you do not know for certain."""
        results_prompt = f"""Context:{results}
                            Set the title for the section as '#Results'
                            
                            __
                            You are a summarizing AI. Please summarize the above results section from a research paper. Focus on the key findings, data trends, and any significant outcomes.
                            Ensure that the summary is concise and accurately reflects the main results and their implications.
                            Output the key results in a bulletpoint format.
                            __
                            
                            Do not output anything you do not know for certain."""
        discussion_prompt = f"""Context:{discussion}
                                Set the title for the section as '#Discussion'
                                __
                                You are a summarizing AI. Please summarize the above discussion section of a research paper. Highlight the key interpretations, implications, and 
                                any connections mde to the broader research context. Ensure the summary is concise and captures the essence of the authors' conclusions.
                                
                                Do not output anything you do not know for certain."""
        references_prompt = f"""Context:{references}
                                Set the title for the section as '#References'
                                    
                                __
                                Iterate through every reference provided. 
                                Only include the name of each paper. 
                                __
                                
                                Do not output anything you do not know for certain."""

        title_response = self.generate_llm_summary('llama3_test4', title_prompt)
        print(title_response)
        author_response = self.generate_llm_summary('llama3_test4', author_prompt)
        print(author_response)
        summary_response = self.generate_llm_summary('llama3_test4', summary_prompt)
        print(summary_response)
        background_significance_response = self.generate_llm_summary('llama3_test4', background_significance_prompt)
        print(background_significance_response)
        methods_response = self.generate_llm_summary('llama3_test4', methods_prompt)
        print(methods_response)
        results_response = self.generate_llm_summary('llama3_test4', results_prompt)
        print(results_response)
        discussion_response = self.generate_llm_summary('llama3_test4', discussion_prompt)
        print(discussion_response)
        references_response = self.generate_llm_summary('llama3_test4', references_prompt)
        print(references_response)

        organized_sections = (title_response + '\n\n\n' + 
                            author_response + '\n\n\n' + 
                            summary_response + '\n\n\n' + 
                            background_significance_response + '\n\n\n' + 
                            methods_response + '\n\n\n' + 
                            results_response + '\n\n\n' + 
                            discussion_response + '\n\n\n' + 
                            references_response)
        
        with open(os.path.join(subfolder_path, "llm_output.txt"), 'w', encoding='utf-8') as file:
            file.write(organized_sections)

        print(f"Summarization complete for {file_name}. Output saved to {os.path.join(subfolder_path, 'llm_output.txt')}")

if __name__ == "__main__":
    directory = input("Enter the path for the folder holding the pdfs you would like to summarize: ")

    # Extract images and text from PDFs
    extractor = PDFExtractor(directory)
    extractor.extract_images_and_text()

    # Process Markdown files
    markdown_processor = MarkdownProcessor(directory)
    markdown_processor.process_files()




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
    categories = ['abstract', 'discussion', 'references', 'conclusion', 'introduction','results', 'methodologies', 'methods', 'methodology', 'background']

    def __init__(self, directory):
        self.directory = directory

    @staticmethod
    def split_markdown_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        sections = []
        current_section = []

        for line in content.splitlines():
            if line.startswith(('**', '##', '#')):
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
                        organized_sections = self.organize_sections(sections, file_path)
                        
                        # Now pass the texts to the summarize_sections method
                        self.summarize_sections(
                            subfolder_path, sections, file_name,
                            organized_sections.get('summary', ''),
                            organized_sections.get('background_significance', ''),
                            organized_sections.get('methods', ''),
                            organized_sections.get('results', ''),
                            organized_sections.get('discussion', ''),
                            organized_sections.get('references', ''),
                        )


    def organize_sections(self, sections, file_path):
        category_sections = {}
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines_list = file.readlines()

        for section in sections:
            lines = section.splitlines()
            title2 = lines[:6]
            title = '\n'.join(title2)
            for category in self.categories:
                if category in title.lower():
                    category_sections[category] = section

        methods2 = []
        results2 = []
        in_methods = False
        in_results = False

        for line in lines_list:
            if 'Methods' in line:
                in_methods = True
                continue  # Skip the line containing 'Methods'
            if 'Results' in line:
                in_results = True
                in_methods = False
                continue  # Skip the line containing 'Results'
            if 'Discussion' in line or 'Conclusion' in line or 'References' in line:
                in_results = False
                break  # Stop if we've reached the Discussion or Conclusion

            if in_methods:
                methods2.append(line)
            elif in_results:
                results2.append(line)

        methods_text = ''.join(methods2).strip()
        results_text = ''.join(results2).strip()

        if len(methods_text.strip()) == 0:
            methods_text = category_sections.get('methods')
            if len(methods_text.strip()) == 0:
                methods_text = category_sections.get('methodologies')
                if len (methods_text.strip()) == 0:
                    methods_text = category_sections.get('methodology') or ''
                    
        if len(results_text.strip()) == 0:
            results_text = category_sections.get('results') or ''
            
        if len(methods_text.strip()) == 0 and len(results_text.strip()) == 0:
            intro_index = next((i for i, sec in enumerate(sections) if 'introduction' in sec.lower()), None)
            results_index = next((i for i, sec in enumerate(sections) if 'results' in sec.lower()), None)
            discussion_index = next((i for i, sec in enumerate(sections) if 'discussion' in sec.lower()), None)

            # Define methods and results sections
            if intro_index is not None:
                if results_index is not None:
                    methods_text = "\n".join(sections[intro_index + 1:results_index])
                    results_text = sections[results_index]
                elif discussion_index is not None:
                    methods_text = "\n".join(sections[intro_index + 1:discussion_index])
                    results_text = "\n".join(sections[results_index:discussion_index])
                else:
                    methods_text = "\n".join(sections[intro_index + 1:])

        if len(results_text.strip()) == 0:
            results_text = category_sections.get('results') or ''
    
        abstract = '\n'.join(sections[:15])
        introduction = category_sections.get('introduction') or ''
        conclusion = category_sections.get('conclusion') or ''
        discussion2 = category_sections.get('discussion') or ''
        references = category_sections.get('references') or ''

        if len(discussion2.strip()) == 0:
            discussion2 = conclusion
        
        if len(introduction.strip()) == 0:
            introduction = category_sections.get('background') or ''
        # Return organized sections
        return {
            'summary': "\n\n\n".join([abstract, introduction, conclusion]),
            'background_significance': introduction + '\n\n\n',
            'methods': methods_text + '\n\n\n', #getting the error cannot concatenate list to string object
            'results': results_text,
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
        author = '\n'.join(sections[0:4])
        
        title1 = '\n'.join(title1) if isinstance(title1, list) else title1
        author = '\n'.join(author) if isinstance(author, list) else author
        summary = '\n'.join(summary) if isinstance(summary, list) else summary
        background_significance = '\n'.join(background_significance) if isinstance(background_significance, list) else background_significance
        methods = '\n'.join(methods) if isinstance(methods, list) else methods
        results = '\n'.join(results) if isinstance(results, list) else results
        discussion = '\n'.join(discussion) if isinstance(discussion, list) else discussion
        references = '\n'.join(references) if isinstance(references, list) else references

        organized_sections = ('#Title\n\n\n' + title1 + '\n\n\n' + '#Authors\n\n\n' +
                            author + '\n\n\n' + '#Summary\n\n\n' +
                            summary + '\n\n\n' + '#Background and Significance\n\n\n' +
                            background_significance + '\n\n\n' + '#Methods\n\n\n' +
                            methods + '\n\n\n' + '#Results\n\n\n' +
                            results + '\n\n\n' + '#Discussion\n\n\n' +
                            discussion + '\n\n\n' + '#References\n\n\n' +
                            references)
        
        with open(os.path.join(subfolder_path, "before.txt"), 'w', encoding='utf-8') as file:
            file.write(organized_sections)
        
        print(f"Segmentation complete for {file_name}. Output saved to {os.path.join(subfolder_path, 'before.txt')}")
        
        title_prompt = f"Context:{title1}" + self.get_title_prompt() #basically goes through the class, grabs function, and carries out the function)
        author_prompt = f"Context{author}" + self.get_author_prompt()
        summary_prompt = f"Context:{summary}" + self.get_summary_prompt()
        background_significance_prompt = f"Context:{background_significance}" + self.get_background_significance_prompt()
        methods_prompt = f"Context:{methods}" + self.get_methods_prompt()
        results_prompt = f"Context:{results}" + self.get_results_prompt()
        discussion_prompt = f"Context:{discussion}" + self.get_discussion_prompt()
        references_prompt = f"Context:{references}" + self.get_references_prompt()

        title_response = self.generate_llm_summary('llama3_fine-tune_test', title_prompt)
        author_response = self.generate_llm_summary('llama3_fine-tune_test', author_prompt)
        summary_response = self.generate_llm_summary('llama3_fine-tune_test', summary_prompt)
        background_significance_response = self.generate_llm_summary('llama3_fine-tune_test', background_significance_prompt)
        methods_response = self.generate_llm_summary('llama3_fine-tune_test', methods_prompt)
        results_response = self.generate_llm_summary('llama3_fine-tune_test', results_prompt)
        discussion_response = self.generate_llm_summary('llama3_fine-tune_test', discussion_prompt)
        references_response = self.generate_llm_summary('llama3_fine-tune_test', references_prompt)
    
        
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
    def get_title_prompt(self):
        return "Set the title for the section as '#Title' Directly state the title of the paper. Disregard all other text."
    def get_author_prompt(self):
        return "Set the title for the section as '#Authors' State the names of the authors with their affiliations ONLY. Disregard all other information."
    def get_summary_prompt(self):
        return """Set the title for the section as '#Summary'. 
                
                __
                You are a summarizing AI tasked with summarizing key sections of a research paper. Please summarize the abstract, introduction, and conclusion into a single concise paragraph. 
                Focus on capturing the main objectives, methods, key findings, and conclusions from the abstract; the background, research question, and significance from the introduction;
                and the key results, implications, and future directions from the conclusion. 
                Ensure the summary is clear, specific, and informative without including unnecessary details.
                __
                
                Do not output anything you do not know for certain."""
    def get_background_significance_prompt(self):
        return """Set the title for the section as '#Background and Significance'
                
                __
                You are a summarizing AI. Please summarize the provided introduction focusing on the background and significance of the study. 
                Highlight the context, the research problem, key literature, and the importance of the study. Ensure the summary captures the rationale behind the research
                and its potential impact or contribution to the field, presented as a clean and concise background and significance section.
                __
                
                Do not output anything you do not know for certain."""
    def get_methods_prompt(self):
        return """Set the title for the section as '#Methods'
                
                __
                You are a summarizing AI. Please summarize the methods section (the provided section), focusing on the experimental design, procedures, materials, and techniques used in the study. 
                Ensure the summary captures the key steps, methodologies, and any relevant parameters or controls, presented as a clear and concise methods section.
                Output everything in a bulletpoint format.
                __
                
                Do not output anything you do not know for certain."""
    def get_results_prompt(self):
        return """"Set the title for the section as '#Results'
                
                __
                You are a summarizing AI. Please summarize the above results section from a research paper. Focus on the key findings, data trends, and any significant outcomes.
                Ensure that the summary is concise and accurately reflects the main results and their implications.
                Output the key results in a bulletpoint format.
                __
                
                Do not output anything you do not know for certain."""
    def get_discussion_prompt(self):
        return """Set the title for the section as '#Discussion'
                __
                You are a summarizing AI. Please summarize the above discussion section of a research paper. Highlight the key interpretations, implications, and 
                any connections made to the broader research context. Ensure the summary is concise and captures the essence of the authors' conclusions.
                __
                
                Do not output anything you do not know for certain.
                """
    def get_references_prompt(self):
        return """Set the title for the section as '#References'
                    
                __
                Iterate through every reference provided. 
                Only include the name of each paper. 
                __
                
                Do not output anything you do not know for certain."""

if __name__ == "__main__":
    directory = input("Enter the path for the folder holding the pdfs you would like to summarize: ")
    extractor = PDFExtractor(directory) #carry out class and main function underneath it (excluding static methods)
    extractor.extract_images_and_text()
    markdown_processor = MarkdownProcessor(directory)
    markdown_processor.process_files()

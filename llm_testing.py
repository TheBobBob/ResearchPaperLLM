import os
import ollama
from pdf_download import output_folder
import re

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

# Make this so that it is mutually exclusive and that sometimes it might not be equal
categories = ['abstract', 'methods', 'methodology', 'discussion', 'references', 'conclusion', 'introduction', 'methodologies', 'results']

directory = rf"C:\Users\navan\Downloads\Data Extraction\{output_folder}"

for subfolder in os.listdir(directory):
    subfolder_path = os.path.join(directory, subfolder)
    if os.path.isdir(subfolder_path):
        print(f"Found directory: {subfolder_path}")

        for file_name in os.listdir(subfolder_path):
            if file_name.endswith('.md'):
                file_path = os.path.join(subfolder_path, file_name)
                print(f"Found Markdown file: {file_path}")

                sections = split_markdown_file(file_path)

                category_sections = {}
                combined_text_for_test = ""

                summary = ""
                background_significance = ""
                methods = ""
                results = ""
                discussion = ""
                references = ""

                for section in sections:
                    text = section.splitlines()
                    title = text[0]
                    title1 = sections[0:5]
                    author = sections[1:4]
                    
                    for category in categories:
                        if category in title.lower():
                            category_sections[category] = section

                methods2 = category_sections.get('methods') or None
                methodology = category_sections.get('methodology') or None
                methodologies = category_sections.get('methodologies') or None

                # Locate 'introduction' and 'results' sections
                intro_index = next((i for i, sec in enumerate(sections) if 'introduction' in sec.lower()), None)
                results_index = next((i for i, sec in enumerate(sections) if 'results' in sec.lower()), None)

                if intro_index is not None and results_index is not None:
                    # Directly assign the methods section from between 'introduction' and 'results'
                    methods = "\n".join(sections[intro_index + 1:results_index])
                else:
                    print(f"Could not find both 'introduction' and 'results' sections in {file_name}.")
                    methods = ''

                # Now combine the sections that were found
                for section in category_sections.values():
                    combined_text_for_test += section + "\n"

                abstract = category_sections.get('abstract') or ''
                introduction = category_sections.get('introduction') or ''
                conclusion = category_sections.get('conclusion') or ''
                results2 = category_sections.get('results') or ''
                discussion2 = category_sections.get('discussion') or ''
                references2 = category_sections.get('references') or ''
                print(abstract)
                print(introduction)
                print(conclusion)
                print(results2)
                print(discussion2)
                print(references2)
                
                summary = (
                    abstract + '\n\n\n' +
                    introduction + '\n\n\n' +
                    conclusion
                )
                background_significance = introduction + '\n\n\n'
                methods += methods2 or methodology or methodologies + '\n\n\n'  # If methods is assigned from the fallback, this will add spacing
                results = results2
                discussion = discussion2
                references = references2
                
                organized_input = summary + '\n\n\n' + methods + '\n\n\n' + results + '\n\n\n' + discussion + '\n\n\n' + references
                with open(os.path.join(subfolder_path, "before.txt"), 'w', encoding='utf-8') as before_file:
                    before_file.write(organized_input)

                # LLM generation for each section
                title_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {title1}
                    
                    Include the words "#Title" at the beginning of the summary. 
                    Directly state the title of the paper using the above input. 
                    Do not include any extra text explaining the title.
                    Only copy and paste the title of the paper.
                    DISREGARD ALL OTHER INFORMATION.
                    """
                )
                title_llm = title_llm1['response']
                print(title_llm)

                author_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {author}
                    
                    Include the words "#Author" at the beginning of the summary.
                    Use the above input and state the names of the authors with their affiliations ONLY.
                    Disregard all other information and ONLY EXTRACT INFORMATION ABOUT THE AUTHORS.
                    """
                )
                author_llm = author_llm1['response']
                print(author_llm)

                summary_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {summary}
                    
                    You are a summarizing AI. Include the words "#Summary" at the beginning of the summary. 
                    Summarize the above input in a succinct way, explaining all mathematical functions and defining all terms.
                    There is no limit to the number of words you can use.
                    Do not include the final paragraph of the conclusion section.
                    """
                )
                summary_llm = summary_llm1['response']
                print(summary_llm)

                background_significance_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {background_significance}
                    
                    You are a summarizing AI. Include the words "#Background and Significance" at the beginning of the summary. 
                    Summarize the provided text in a succinct way, being as specific as possible.
                    There is no limit on the number of words you can use.
                    """
                )
                background_significance_llm = background_significance_llm1['response']
                print(background_significance_llm)

                methods_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {methods}
                    
                    You are a summarizing AI. Include the words "#Methods" at the beginning of the summary. 
                    Summarize the provided text in a succinct way, be as specific as possible.
                    Provide the steps outlined in the text in a list format. 
                    There is no limit to the number of words you can use.
                    """
                )
                methods_llm = methods_llm1['response']
                print(methods_llm)

                results_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {results}
                    
                    You are a summarizing AI. Include the words "#Results" at the beginning of the summary.
                    Summarize the provided text in a succinct way, be as specific as possible.
                    Provide the key findings of the section in a bulleted list, along with the general summary. 
                    There is no limit to the number of words you can use.
                    """
                )
                results_llm = results_llm1['response']
                print(results_llm)

                discussion_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {discussion}
                    
                    You are a summarizing AI. Include the words "#Discussion" at the beginning of the summary. 
                    Summarize the provided text in a succinct way, be as specific as possible. 
                    Provide the key points in a bulleted list along with the general summary. 
                    There is no limit to the number of words you can use.
                    """
                )
                discussion_llm = discussion_llm1['response']
                print(discussion_llm)

                references_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {references}
                    
                    Include the words "#References" at the beginning of the summary. 
                    For every reference, provide ONLY the name of the paper. 
                    """
                )
                references_llm = references_llm1['response']
                print(references_llm)

                all_text = "\n\n\n\n\n\n#".join([
                    title_llm, author_llm, summary_llm, 
                    background_significance_llm, methods_llm, 
                    results_llm, discussion_llm, references_llm
                ])

                output_file_path = os.path.join(subfolder_path, f"{os.path.splitext(file_name)[0]}_summary.txt")

                with open(output_file_path, 'w', encoding='utf-8') as file:
                    file.write(all_text)

                print(f"Summarization complete for {file_name}. Output saved to {output_file_path}")

print("All files processed.")


#looks great!!
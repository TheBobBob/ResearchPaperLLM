
import os
import ollama
from pdf_download import output_folder
import re

# Directory where subfolders with Markdown files are located
directory = rf"C:\Users\navan\Downloads\Data Extraction\{output_folder}"
#categories = ['abstract', 'methods', 'methodology', 'discussion', 'references', 'conclusion', 'introduction', 'methodologies']

for subfolder in os.listdir(directory):
    subfolder_path = os.path.join(directory, subfolder)
    if os.path.isdir(subfolder_path):
        print(f"Found directory: {subfolder_path}")

        for file_name in os.listdir(subfolder_path):
            if file_name.lower().endswith('.txt'):  # Strictly check for '.txt' files
                file_path = os.path.join(subfolder_path, file_name)
                print(f"Found txt file: {file_path}")
                
                # Read the contents of the Markdown file
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()

                # Generate summary using Ollama
                text_llm1 = ollama.generate(
                    model="llama3", 
                    prompt=f"""
                    Context: {text} 
                    
                    Organize each section in the provided research paper into the following overarching sections. Delimit each organized section by **. 
                    Do not summarize or alter the input in any way.
                    
                    Sections for the input text to be organized into.
                    1. Title
                    2. Authors 
                    3. Abstract
                    4. Introduction 
                    5. Methods
                    6. Results
                    7. Conclusion
                    8. Discussion
                    9. References
                    
                    """
                )
                
                text_llm = text_llm1['response']
                print(text_llm)

                # Save the summarized output to a text file
                output_file_path = os.path.join(subfolder_path, f"{os.path.splitext(file_name)[0]}_sectioned.txt")
                with open(output_file_path, 'w', encoding='utf-8') as file:
                    file.write(text_llm)

                print(f"Segmentation complete for {file_name}. Output saved to {output_file_path}")
                
                with open(output_file_path, 'r', encoding = 'utf-8') as file:
                    text = file.read()
                
                sections = text.split('\n**')
                
                title = sections[0]
                authors = sections[1]
                abstract = sections[2]
                introduction = sections[3]
                methods = sections[4]
                results = results[5]
                conclusion = sections[6]
                discussion = sections[7]
                references = sections[8]
                
                
                title = title + '\n\n\n'
                authors = authors + '\n\n\n'
                summary = (
                    abstract + '\n\n\n' +
                    introduction + '\n\n\n' +
                    conclusion
                )
                background_significance = introduction + '\n\n\n'
                methods = methods + '\n\n\n'
                results = results + '\n\n\n'
                discussion = discussion + '\n\n\n'
                references = references + '\n\n\n'
                
                title_llm1 = ollama.generate(
                    model="llama3", prompt=f"""
                    Context: {title}
                    
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
                    Context: {authors}
                    
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



'''
prompt 1:
Organize each section in this txt file (delimited by ** or ## or # or *) into the following sections (give sections)

save everything into a file, and have it delimit by #

Then take that output text file, split into sections based on their title, then organize into the sections, pass into LLM

'''

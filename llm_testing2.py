import os
import ollama
from pdf_download import output_folder
import re

# Directory where subfolders with Markdown files are located
directory = rf"C:\Users\navan\Downloads\Data Extraction\{output_folder}"

for subfolder in os.listdir(directory):
    subfolder_path = os.path.join(directory, subfolder)
    if os.path.isdir(subfolder_path):
        print(f"Found directory: {subfolder_path}")

        for file_name in os.listdir(subfolder_path):
            if file_name.lower().endswith('.md'):  # Strictly check for '.md' files
                file_path = os.path.join(subfolder_path, file_name)
                print(f"Found Markdown file: {file_path}")
                
                # Read the contents of the Markdown file
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()

                # Generate summary using Ollama
                text_llm1 = ollama.generate(
                    model="llama3", 
                    prompt=f"""
                    Context: {text}
                    
                    You are a summarizing AI. The context provided is the text of a research paper that you will be summarizing in sections. 
                    
                    Section 1:
                    This is only the title of the paper copy and pasted. 
                    _________________
                    Include the words "#Title" at the beginning of the summary. 
                    Directly state the title of the paper using the above input. 
                    Do not include any extra text explaining the title.
                    Only copy and paste the title of the paper.
                    DISREGARD ALL OTHER INFORMATION.
                    
                    Section 2:
                    This is only the authors' and their affiliations copy and pasted. 
                    _________________
                    Include the words "#Author" at the beginning of the summary.
                    Use the above input and state the names of the authors with their affiliations ONLY.
                    Disregard all other information and ONLY EXTRACT INFORMATION ABOUT THE AUTHORS OF THE PAPER. 
                    This will be located towards the top of the text. DISREGARD THE REFERENCES AT THE BOTTOM OF THE TEXT. 
                    
                    Section 3:
                    This is a summary of the paper that will consist of the introduction, abstract, and conclusion.
                    _________________
                    You are a summarizing AI. Include the words "#Summary" at the beginning of the summary. 
                    Summarize the input in a succinct way, explaining all mathematical functions and defining all terms.
                    There is no limit to the number of words you can use.
                    Do not include the final paragraph of the conclusion section.
                    ONLY INCLUDE THE ABSTRACT, CONCLUSION, AND INTRODUCTION IN THE TEXT. 
                    
                    Section 4:
                    This is a summary of the introduction of the paper which will serve as the background and significance.
                    
                    _________________
                    You are a summarizing AI. Include the words "#Background and Significance" at the beginning of the summary. 
                    Summarize the provided text in a succinct way, being as specific as possible.
                    There is no limit on the number of words you can use.
                    ONLY EXTRACT AND SUMMARIZE THE INTRODUCTION. DISREGARD ALL OTHER TEXT. 
                    
                    Section 5:
                    This is a summary of the methods section of the paper. 
                    _________________
                    You are a summarizing AI. Include the words "#Methods" at the beginning of the summary. 
                    Summarize the provided text in a succinct way, be as specific as possible.
                    Provide the steps outlined in the text in a list format. 
                    There is no limit to the number of words you can use.
                    ONLY EXTRACT AND EXPLAIN THE METHODS SECTION. DISREGARD ALL OTHER TEXT. 
                    IF THE METHODS SECTION IS NOT EXPLICITLY DEFINED, EXTRACT AND EXPLAIN THE SECTIONS BETWEEN THE INTRODUCTION AND THE RESULTS.
                    
                    Section 6: 
                    This is a summary of the results section of the paper.
                    _________________
                    You are a summarizing AI. Include the words "#Results" at the beginning of the summary.
                    Summarize the provided text in a succinct way, be as specific as possible.
                    Provide the key findings of the section in a bulleted list, along with the general summary. 
                    There is no limit to the number of words you can use.
                    ONLY EXTRACT AND EXPLAIN THE RESULTS SECTION OF THE PAPER, DISREGARD ALL OTHER TEXT. 
                    
                    Section 7:
                    This is a summary of the discussion section of the paper. 
                    _________________
                    You are a summarizing AI. Include the words "#Discussion" at the beginning of the summary. 
                    Summarize the provided text in a succinct way, be as specific as possible. 
                    Provide the key points in a bulleted list along with the general summary. 
                    There is no limit to the number of words you can use.
                    ONLY EXTRACT AND EXPLAIN THE DISCUSSION SECTION OF THE PAPER, DISREGARD ALL OTHER TEXT. 
                    
                    Section 8:
                    This is a summary of the references section of the paper. 
                    _________________
                    Include the words "#References" at the beginning of the summary. 
                    For every reference, provide ONLY the name of the paper. 
                    DISREGARD ALL OTHER TEXT EXCEPT FOR THE REFERENCES. 
                    """
                )
                
                text_llm = text_llm1['response']
                print(text_llm)

                # Save the summarized output to a text file
                output_file_path = os.path.join(subfolder_path, f"{os.path.splitext(file_name)[0]}_summary.txt")
                with open(output_file_path, 'w', encoding='utf-8') as file:
                    file.write(text_llm)

                print(f"Summarization complete for {file_name}. Output saved to {output_file_path}")
                
                
#didnt really work bc it gets overwhelmed for some reason??
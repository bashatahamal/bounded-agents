import re

def read_markdown_file_to_dict(file_path):
    # Read the content of the Markdown file
    with open(file_path, 'r', encoding='utf-8') as file:
        markdown_text = file.read()
    
    # Call the existing function to process the Markdown text
    return read_markdown_to_dict(markdown_text)

def read_markdown_to_dict(markdown_text):
    # Initialize an empty dictionary to store the data
    data_dict = {}
    
    # Split the markdown text into sections based on the heading patterns
    sections = re.split(r'^##\s+', markdown_text, flags=re.MULTILINE)[1:]
    
    # Iterate over the sections to extract headings and content
    for section in sections:
        # Split each section into lines
        lines = section.split('\n')
        
        # Extract the heading
        heading = lines[0]
        
        # Extract the content (excluding the heading and empty lines)
        content = '\n'.join(lines[1:]).strip()
        
        # Store the heading and content in the dictionary
        data_dict[heading] = content
    
    return data_dict

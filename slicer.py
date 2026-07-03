import os
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# Initialize the parser globally so it doesn't reload for every single file
PY_LANGUAGE = Language(tspython.language())
parser = Parser()
parser.language = PY_LANGUAGE

query_string = """
(function_definition
  name: (identifier) @name
) @function
"""
query = PY_LANGUAGE.query(query_string)

def extract_python_functions(directory_path):
    """Walks a directory, parses .py files, and returns a list of functions."""
    extracted_data = []
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                
                with open(filepath, "rb") as f:
                    raw_code = f.read()
                
                tree = parser.parse(raw_code)
                matches = query.captures(tree.root_node)
                
                if "function" in matches:
                    for node in matches["function"]:
                        func_text = raw_code[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
                        
                        # Append as a dictionary so we keep the filename with the code
                        extracted_data.append({
                            "file": file,
                            "code": func_text
                        })
                        
    return extracted_data
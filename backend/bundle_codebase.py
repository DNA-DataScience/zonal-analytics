import os

def bundle_codebase(output_filename="codebasev2.md", root_dir="."):
    # 1. Configuration: Directories and extensions to completely ignore
    IGNORE_DIRS = {
        '.git', '.vscode', '.idea', '__pycache__', 'node_modules', 
        '.venv', 'venv', 'env', 'build', 'dist', 'out', 'target'
    }
    
    IGNORE_EXTS = {
        # Binaries & Images
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.pdf',
        '.zip', '.tar', '.gz', '.mp4', '.mp3', '.env',
        # Compiled code
        '.pyc', '.pyo', '.exe', '.dll', '.so', '.dylib', '.class', '.jar',
        # Lock files and databases
        '.lock', '.sqlite', '.db', '.sqlite3'
    }

    # Open the output file in write mode with UTF-8 encoding
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        
        # 2. os.walk traverses the directory tree top-down
        for current_root, dirs, files in os.walk(root_dir):
            
            # 3. Prune the directory tree in-place
            # We iterate backward to safely remove items from the list we are looping over
            for i in range(len(dirs) - 1, -1, -1):
                if dirs[i] in IGNORE_DIRS or dirs[i].startswith('.'):
                    del dirs[i]
            
            # 4. Process the files in the current directory
            for file in files:
                # Skip the script itself and the output file to prevent infinite loops
                if file == "bundle_code.py" or file == output_filename:
                    continue
                
                # Extract the file extension (e.g., '.py') in lowercase
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                
                # Skip ignored extensions or hidden files (like .DS_Store)
                if ext in IGNORE_EXTS or file.startswith('.'):
                    continue
                
                # Construct the full path and the relative path (for cleaner display)
                file_path = os.path.join(current_root, file)
                rel_path = os.path.relpath(file_path, root_dir)
                
                # 5. Defensively read the file and write to Markdown
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        
                    # Write the formatted output
                    outfile.write(f"### File: `{rel_path}`\n\n")
                    # If we know the language, we can pass the extension (without the dot) for syntax highlighting
                    lang = ext[1:] if ext else ""
                    outfile.write(f"```{lang}\n")
                    outfile.write(content)
                    # Add a trailing newline to ensure the code block closes properly
                    if not content.endswith('\n'):
                        outfile.write('\n')
                    outfile.write("```\n\n---\n\n")
                    
                except UnicodeDecodeError:
                    # If a file is binary but slipped past our extension check, catch it here
                    print(f"Skipped non-UTF8 file: {rel_path}")
                except Exception as e:
                    # Catch permission errors or symlink loops
                    print(f"Error reading {rel_path}: {e}")

    print(f"Successfully bundled codebase into {output_filename}")

if __name__ == "__main__":
    bundle_codebase()
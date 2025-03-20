import os
import json
import csv
import pandas as pd
from airr import read_airr

# ---------------- Helper Functions ---------------- #

def get_paths(base_path):
    """Generates file paths for metadata processing."""
    return {
        "metadata": os.path.join(base_path, 'metadata.json'),
        "biosample_output": os.path.join(base_path, 'biosample.tsv'),
        "sra_output": os.path.join(base_path, 'sra.tsv'),
        "bioproject_output": os.path.join(base_path, 'bioproject.tsv'),
        "biosample_json_format": r'AIRR_BioSample_v1.0.json',
        "sra_json_format": r'AIRR_SRA_v1.0.json',
        "bioproject_json_format": r'PROJECT.json',
        "xlsx_output_path": os.path.join(base_path, 'metadata.xlsx')
    }

def create_columns(tsv_file, format):
    """Writes column headers to a TSV file."""
    writer = csv.writer(tsv_file, delimiter='\t')
    writer.writerow(format.keys())

def write_row(tsv_file, row):
    """Writes a row to a TSV file."""
    writer = csv.writer(tsv_file, delimiter='\t')
    writer.writerow(row)

# ---------------- Metadata Processing ---------------- #

def process_metadata(paths, json_format_key, output_key, process_function):
    """Reads metadata and writes formatted TSV data."""
    try:
        data = read_airr(paths['metadata'])
        with open(paths[output_key], 'w', newline='', encoding='utf-8') as tsv_file, open(paths[json_format_key], 'r', encoding='utf-8') as json_format:
            format = json.load(json_format)
            create_columns(tsv_file, format)
            for repertoire in data['Repertoire']:
                process_function(tsv_file, repertoire, format)
    except Exception as e:
        print(f"Error processing {output_key}: {e}")

def process_repertoire(tsv_file, repertoire, format, check_parent_child_func):
    """Processes and writes a row for a given metadata category."""
    tsv_row = []
    for key, value in format.items():
        if value is None:
            tsv_row.append(None)
        elif value in ["AIRR-seq", ""]:
            tsv_row.append(value)
        elif '.' in value:
            parent, child = value.split('.')[:2]
            new_value = check_parent_child_func(parent, child, value, repertoire)
            tsv_row.append(new_value)
        else:
            tsv_row.append(repertoire.get(value, ''))
    write_row(tsv_file, tsv_row)

def check_parent_child(parent, child, value, repertoire):
    """Handles nested JSON structures in metadata."""
    try:
        parent_obj = repertoire.get(parent, {})
        
        # If parent_obj is a list, take the first element
        if isinstance(parent_obj, list) and len(parent_obj) > 0:
            first_parent = parent_obj[0]  # Get the first element
            
            if isinstance(first_parent, dict):  # Ensure it's a dictionary
                if len(value.split('.')) == 3:
                    grandson = value.split('.')[2]
                    child_obj = first_parent.get(child, {})
                    
                    if isinstance(child_obj, list) and len(child_obj) > 0:
                        return child_obj[0].get(grandson, '')  # Get first element's grandson if it's a list
                    elif isinstance(child_obj, dict):
                        return child_obj.get(grandson, '')  # Get the value if it's a dictionary
                    return ''  # If child_obj is neither a dict nor a list, return empty
                    
                return first_parent.get(child, '')  # Handle standard parent-child case
            
            elif isinstance(first_parent, list):  # Handle case where parent itself is a list of lists
                return first_parent  # Return as is, or modify depending on expected format

        elif isinstance(parent_obj, dict):  # If it's a dictionary, fetch child normally
            return parent_obj.get(child, '')
        
    except Exception as e:
        print(f"Problem with {value}: {e}")
    return ''


def check_parent_child_old(parent, child, value, repertoire):
    """Handles nested JSON structures in metadata."""
    try:
        parent_obj = repertoire.get(parent, {})
        if isinstance(parent_obj, list) and len(parent_obj) > 0:
            first_parent = parent_obj[0]
            if len(value.split('.')) == 3:
                grandson = value.split('.')[2]
                return first_parent.get(child, {}).get(grandson, '')
            return first_parent.get(child, '')
        return parent_obj.get(child, '')
    except Exception as e:
        print(f"Problem with {value}: {e}")
    return ''

# ---------------- File-Specific Processing ---------------- #

def airr_biosample(paths):
    process_metadata(paths, 'biosample_json_format', 'biosample_output', lambda tsv_file, r, f: process_repertoire(tsv_file, r, f, check_parent_child))

def airr_sra(paths):
    process_metadata(paths, 'sra_json_format', 'sra_output', lambda tsv_file, r, f: process_repertoire(tsv_file, r, f, check_parent_child))

def airr_bioproject(paths):
    process_metadata(paths, 'bioproject_json_format', 'bioproject_output', lambda tsv_file, r, f: process_repertoire(tsv_file, r, f, check_parent_child))

# ---------------- Excel File Creation ---------------- #

def create_metadata_xlsx(paths):
    """Combines TSV files into an Excel file."""
    xlsx_output_path = paths["xlsx_output_path"]
    try:
        dfs = {
            "sra": pd.read_csv(paths["sra_output"], sep='\t'),
            "biosample": pd.read_csv(paths["biosample_output"], sep='\t'),
            "bioproject": pd.read_csv(paths["bioproject_output"], sep='\t')
        }
        with pd.ExcelWriter(xlsx_output_path, engine='openpyxl') as writer:
            for sheet, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet, index=False)
    except Exception as e:
        print(f"Error creating Excel file: {e}")

# ---------------- Main Execution ---------------- #

def generate_metadata(base_path):
    
    # Define the required JSON files
    required_files = {'AIRR_BioSample_v1.0.json', 'AIRR_SRA_v1.0.json', 'PROJECT.json'}
    # Get the set of existing files in the directory
    existing_files = set(os.listdir("./"))
    # Check if all required files exist
    if (not required_files.issubset(existing_files)):
        missing_files = required_files - existing_files
        print(f"Missing files: {', '.join(missing_files)}")
 
    paths = get_paths(base_path)
    airr_biosample(paths)
    airr_sra(paths)
    airr_bioproject(paths)
    create_metadata_xlsx(paths)

if __name__ == "__main__":
    PROJECT_NAME = "TEMP"  # Change this if needed
    BASE_PATH = rf'C:\Users\user\Desktop\תואר שני\עבודה אצל גור\metadata2OTSprojects\{PROJECT_NAME}'
    generate_metadata(BASE_PATH)

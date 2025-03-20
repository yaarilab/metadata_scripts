import pandas as pd 
import shutil
import os

from json_to_xlsx import generate_metadata

# Function to merge data by the 'combine_repertoire' column
def merge_by_combine_repertoire(xlsx_path):
    """
    Merges data from an Excel file based on the 'combine_repertoire' column.
    
    Args:
        xlsx_path (str): Path to the Excel file.

    Returns:
        str: Path to the newly created merged Excel file.
    """

    # Load all sheets from the Excel file into a dictionary
    xlsx_data = pd.read_excel(xlsx_path, sheet_name=None)

    # Function to merge rows based on 'combine_repertoire'
    def merge_rows(df, combine_repertoire_series=None):
        if combine_repertoire_series is not None:
            df['combine_repertoire'] = combine_repertoire_series
        
        return df.groupby('combine_repertoire').agg(
            lambda x: '_'.join(x.dropna().astype(str).unique()) if x.nunique() > 1 else x.iloc[0]
        ).reset_index()  # Reset index to keep 'combine_repertoire' as a column
    
    # Function to merge rows, summing 'cell_number' instead of concatenating it
    def merge_rows_t(df, combine_repertoire_series=None):
        if combine_repertoire_series is not None:
            df['combine_repertoire'] = combine_repertoire_series
        
        def custom_agg(x):
            if x.name == 'cell_number':  # Sum cell_number instead of concatenating
                return x.dropna().astype(float).sum()
            else:
                return '_'.join(x.dropna().astype(str).unique()) if x.nunique() > 1 else x.iloc[0]
        
        return df.groupby('combine_repertoire').agg(custom_agg).reset_index()

    # Copy the merging column from 'sra' sheet
    combine_repertoire = xlsx_data['sra']['combine_repertoire']
    flag = None

    # If 'combine_repertoire' is empty, use 'isolate' from 'biosample' instead
    if len(combine_repertoire.dropna()) == 0:
        print("No values found in the 'combine_repertoire' column. Merging by samples instead.\n")
        combine_repertoire = xlsx_data['biosample']['isolate']
        flag = combine_repertoire
    
    # Merge the SRA sheet
    merged_sra = merge_rows(xlsx_data['sra'], flag)

    # Merge the biosample sheet using the combine_repertoire from SRA
    merged_biosample = merge_rows(xlsx_data['biosample'], combine_repertoire)

    # Merge the bioproject sheet using the combine_repertoire from SRA
    merged_bioproject = merge_rows(xlsx_data['bioproject'], combine_repertoire)

    # Create 'union' directory if it doesn't exist
    union_dir = os.path.join(os.path.dirname(xlsx_path), 'union')
    os.makedirs(union_dir, exist_ok=True)

    # Define the new file path in the 'union' directory
    new_xlsx_path = os.path.join(union_dir, 'metadata_after_union.xlsx')

    # Save the updated sheets to a new Excel file
    with pd.ExcelWriter(new_xlsx_path, engine='openpyxl') as writer:
        merged_sra.to_excel(writer, sheet_name='sra', index=False)
        merged_biosample.to_excel(writer, sheet_name='biosample', index=False)
        merged_bioproject.to_excel(writer, sheet_name='bioproject', index=False)

    # Save the merged sheets as TSV files
    merged_sra.to_csv(new_xlsx_path.replace('metadata_after_union.xlsx', 'sra.tsv'), sep='\t', index=False)
    merged_biosample.to_csv(new_xlsx_path.replace('metadata_after_union.xlsx', 'biosample.tsv'), sep='\t', index=False)
    merged_bioproject.to_csv(new_xlsx_path.replace('metadata_after_union.xlsx', 'bioproject.tsv'), sep='\t', index=False)

    return new_xlsx_path
    

def process_file(file_path):
    """
    Processes a given JSON or Excel file:
    - If JSON: Converts it to an Excel metadata file.
    - If Excel: Merges its contents and saves a combined version.

    Args:
        file_path (str): Path to the input file.
    """

    if not os.path.exists(file_path):
        print("Error: The specified file does not exist.\n")
        return
    
    BASE_PATH = os.path.dirname(file_path)

    if file_path.lower().endswith('.json'):
        # If the file is not named 'metadata.json', create a copy with that name
        if os.path.basename(file_path) != "metadata.json":
            shutil.copy(file_path, os.path.join(BASE_PATH, "metadata.json"))
            print("COPY CREATED: Since the JSON filename was not 'metadata.json', a copy was created.\n")
        
        # Generate metadata from the JSON file
        generate_metadata(BASE_PATH)
        file_path = os.path.join(BASE_PATH, "metadata.xlsx")
        print(f"METADATA XLSX CREATED: The JSON file has been processed, and the metadata is saved at '{file_path}'.\n")
        
    if file_path.lower().endswith('.xlsx'):
        # Merge the Excel metadata file
        combined_xlsx_path = merge_by_combine_repertoire(file_path)
        print(
            f"The combined Excel file has been created and saved at: '{combined_xlsx_path}'.\n"
            "TSV files have also been saved in this location.\n"
            "If you want a combined JSON, run 'tsv_to_json'.\n"
            "Make sure to update the location and filename."
        )
    else:
        print("Error: Unsupported file type. Please provide a JSON or Excel file.\n")


if __name__ == "__main__":
    
    temp_path = "C:\\Users\\user\\Desktop\\תואר שני\\עבודה אצל גור\\metadata2OTSprojects\\TEMP\\temp.json"
    
    # Get file path from the user
    #file_path = input("Enter the path to the file: ").strip()
    file_path = temp_path
    # Process the file (JSON or Excel)
    process_file(file_path)



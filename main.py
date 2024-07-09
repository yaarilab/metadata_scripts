import argparse
import airr
import json
import csv
import ast
import numpy

# from airr import load_rearrangement, dump_rearrangement, validate_rearrangement, validate_airr, read_airr

METADATA_PATH = r'metadata.json'
BIOSAMPLE_PATH = r'remove_quotes_biosample.tsv'
SRA_PATH = r'remove_quotes_sra.tsv'
PROJECT_PATH = r'remove_quotes_bioproject.tsv'

BIOSAMPLE_JSON_FORMAT_PATH = r'AIRR_BioSample_v1.0.json'
SRA_JSON_FORMAT_PATH = r'AIRR_SRA_v1.0.json'
PROJECT_JSON_FORMAT_PATH = r'PROJECT.json'

def remove_spaces_from_file(input_file, output_file):
    with open(input_file, 'r') as infile:
        content = infile.read()

    # Remove spaces (replace space character with an empty string)
    content_without_spaces = content.replace(" ", "")

    with open(output_file, 'w') as outfile:
        outfile.write(content_without_spaces)


def remove_quotes_from_columns(input_file, output_file):
    with open(input_file, 'r') as infile:
        lines = infile.readlines()

    # Process each line and remove double quotes from each column
    modified_lines = []
    for line in lines:
        # Split the line into columns based on the tab separator
        columns = line.split('\t')

        # Remove double quotes from each column
        for i in range(len(columns)):
            columns[i] = columns[i].replace('"', '')
        # Join the modified columns back into a line and append to the modified_lines list
        modified_line = '\t'.join(columns)
        modified_lines.append(modified_line)

    with open(output_file, 'w') as outfile:
        outfile.writelines(modified_lines)# Example usage:


input_file_path = 'input.txt'
output_file_path = 'output.txt'

def convert_tsv_to_json():
    data = {'Repertoire': []}
    counter = 0
    rep_list = []
    biosample_reader = airr.read_rearrangement(BIOSAMPLE_PATH)
    sra_reader = airr.read_rearrangement(SRA_PATH)
    project_reader = airr.read_rearrangement(PROJECT_PATH)

    for row in biosample_reader:
        try:
            repertoire = airr.schema.RepertoireSchema.template()
            update_repertoire(row, repertoire, BIOSAMPLE_JSON_FORMAT_PATH)
            rep_list.append(repertoire)
        except Exception as e:
            print(row)
            print(f"Error processing biosample_reader row: {e}")

    # Loop for sra_reader
    for row in sra_reader:
        try:
            update_repertoire(row, rep_list[counter], SRA_JSON_FORMAT_PATH)
            counter += 1
        except Exception as e:
            print(f"Error processing sra_reader row: {e}")

    # Reset counter
    counter = 0

    # Loop for project_reader
    for row in project_reader:
        try:
            update_repertoire(row, rep_list[counter], PROJECT_JSON_FORMAT_PATH)
            data['Repertoire'].append(rep_list[counter])
            counter += 1
        except Exception as e:
            print(f"Error processing project_reader row: {e}")


    json_file_path = 'metadata.json'
    airr.write_airr(json_file_path, data)


def search_key(data, target_key, new_value):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                data[key] = new_value
                return True
            elif isinstance(value, (dict, list)):
                result = search_key(value, target_key, new_value)
                if result:
                    return True
    elif isinstance(data, list):
        for item in data:
            result = search_key(item, target_key, new_value)
            if result:
                return True

    return False


def extract_key(key):
    if '.' in key:
        if len(key.split('.')) == 3:
            return key.split('.')[2]

        return key.split('.')[1]

    return key


def repear_value(value):
    # Check if the value is a string and starts with '{' and ends with '}'
    if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
        try:
            # Safely evaluate the string to convert it to a Python object
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # If there's an error in conversion, return the original value
            return value
    else:
        # Return the value as is if it does not match the pattern
        return value


def update_repertoire(row, repertoire, type):
    not_include = ["AIRR-seq", "", None]

    for key, value in row.items():
        new_key = translate_key(key, type)
        if new_key not in not_include:
            new_key = extract_key(new_key)
            new_key = change_new_key_to_currect_name(new_key)
            value = repear_value(value)
            if not search_key(repertoire, new_key, value):
                repertoire[new_key] = value

    return repertoire


def change_new_key_to_currect_name(new_key):
    if new_key == "age":
        return "age_event"

    return new_key


def translate_key(current_key, type):
    with open(type, 'r') as json_format:
        format = json.load(json_format)

    for key, value in format.items():
        if key == current_key:
            return value

    return None

def convert_string_to_int(data, keys):
    # Check and convert only specific keys
    keys_to_convert = keys  # Add more keys as needed

    def recursive_convert(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in keys_to_convert and isinstance(value, str) and value.isdigit():
                    obj[key] = int(value)
                elif isinstance(value, (dict, list)):
                    recursive_convert(value)
        elif isinstance(obj, list):
            for item in obj:
                recursive_convert(item)

    recursive_convert(data)
    
    return data


def replace_empty_strings_with_null(data):
    if isinstance(data, dict):
        return {k: replace_empty_strings_with_null(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_empty_strings_with_null(i) for i in data]
    elif data == "":
        return None
    return data


if __name__ == "__main__":
    remove_quotes_from_columns('biosample.tsv', 'remove_quotes_biosample.tsv')
    remove_quotes_from_columns('sra.tsv', 'remove_quotes_sra.tsv')
    remove_quotes_from_columns('bioproject.tsv', 'remove_quotes_bioproject.tsv')

    project_reader = airr.read_rearrangement(PROJECT_PATH)
    convert_tsv_to_json()
    with open("metadata.json", 'r') as file:
        json_data = json.load(file)
        key_to_change = ["template_amount", "total_reads_passing_qc_filter", "read_length", "paired_read_length"]
        converted_data  = convert_string_to_int(json_data, key_to_change)
        converted_data = replace_empty_strings_with_null(converted_data)
        json_output = json.dumps(converted_data)
        with open("metadata.json", 'w') as file:
            json.dump(converted_data, file, indent=4)  # Use indent for pretty printing


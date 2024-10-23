###Checks exifread, compares and reports md5 hash of two locations to comparison_report.csv
### Ignores invalid file namess

import os
import hashlib
import pandas as pd

def calculate_md5(file_path):
    """Calculate the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def is_valid_filename(filename):
    """Check if the filename follows the specified naming convention."""
    # Split filename from extension
    name, _ = os.path.splitext(filename)
    valid = name.startswith(('V', 'C')) and name[1:8].isdigit() and name.endswith('F')
    if not valid:
        print(f"Invalid filename skipped: {filename}")
    return valid

def is_valid_file_type(filename):
    """Check if the file type is among the specified types."""
    valid_extensions = ('.jpg', '.dng', '.tif', '.tiff', '.cr2')
    return filename.lower().endswith(valid_extensions)

def compare_directories(dir1, dir2):
    """Compare image files in two directories."""
    report = []

    all_files_dir1 = os.listdir(dir1)
    all_files_dir2 = os.listdir(dir2)

    # Print all files for debugging
    print("All files in Directory 1:")
    print(all_files_dir1)
    
    print("All files in Directory 2:")
    print(all_files_dir2)

    files_dir1 = {f: os.path.join(dir1, f) for f in all_files_dir1
                   if is_valid_filename(f) and is_valid_file_type(f)}
    files_dir2 = {f: os.path.join(dir2, f)
                   for f in all_files_dir2 if is_valid_filename(f) and is_valid_file_type(f)}

    # Debugging: Print the valid filenames found
    print("Valid files in Directory 1:")
    print(files_dir1.keys())

    print("Valid files in Directory 2:")
    print(files_dir2.keys())

    for filename, path1 in files_dir1.items():
        if filename in files_dir2:
            path2 = files_dir2[filename]

            md5_hash1 = calculate_md5(path1)
            md5_hash2 = calculate_md5(path2)

            match = md5_hash1 == md5_hash2
            report.append({'Filename': filename, 'MD5 Hash 1': md5_hash1, 'MD5 Hash 2': md5_hash2, 'Match': match})
        else:
            report.append({'Filename': filename, 'Error': 'Not found in second directory'})

    for filename in files_dir2.keys():
        if filename not in files_dir1:
            report.append({'Filename': filename, 'Error': 'Not found in first directory'})

    return report

def main():
    dir1 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Alliance"
    dir2 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Picturae"
    
    if not os.path.exists(dir1):
        print(f"Directory 1 does not exist: {dir1}")
        return
    if not os.path.exists(dir2):
        print(f"Directory 2 does not exist: {dir2}")
        return

    report = compare_directories(dir1, dir2)

    # Convert report to DataFrame and save to CSV
    df = pd.DataFrame(report)
    df.to_csv('comparison_report.csv', index=False)
    
    if df.empty:
        print("The report is empty. No matching files found.")
    else:
        print('Comparison report saved to comparison_report.csv')

if __name__ == '__main__':
    main()

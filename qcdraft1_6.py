######## Issues with corruption reporting.  For some reason file name errors are being reported in corrupt image folder and csv.
######## Need to correct output.  ALSO not sure if the script is working with corrupted files.  Need to test with actually corrupted dngs
######## Check in EMu for "files to delete group" for files to use


### 1 Compares and checks all images between 2 directories to make sure all files are identical by filename and MD5 HASH
### 2 Any comparison errors are moved, reported and recopied from Picturae
### 3 Errors with file names are moved, and reported
### 4 Corruption is checked and files are moved, and reported

import os
import hashlib
import pandas as pd
import shutil
import re
import cv2

def calculate_md5(file_path):
    """Calculate the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def is_valid_file_type(filename):
    """Check if the file type is among the specified types."""
    valid_extensions = ('.jpg', '.jpeg', '.dng', '.tif', '.tiff', '.cr2')
    return filename.lower().endswith(valid_extensions)

def is_valid_filename(filename):
    """Check if the filename adheres to the naming convention."""
    return bool(re.match(r'^[VC]\d{7}F$', filename[:-4]))  # Exclude the file extension

def is_image_corrupted(file_path):
    """Check if the image is corrupted or unreadable."""
    image = cv2.imread(file_path)
    return image is None

def compare_directories(dir1, dir2):
    """Compare image files in two directories."""
    report = []
    unmatched_files = []

    all_files_dir1 = os.listdir(dir1)
    all_files_dir2 = os.listdir(dir2)

    files_dir1 = {f: os.path.join(dir1, f) for f in all_files_dir1 if is_valid_file_type(f)}
    files_dir2 = {f: os.path.join(dir2, f) for f in all_files_dir2 if is_valid_file_type(f)}

    identical = True  # Flag to check if directories are identical

    for filename, path1 in files_dir1.items():
        if filename in files_dir2:
            path2 = files_dir2[filename]

            md5_hash1 = calculate_md5(path1)
            md5_hash2 = calculate_md5(path2)

            match = md5_hash1 == md5_hash2
            report.append({'Filename': filename, 'MD5 Hash 1': md5_hash1, 'MD5 Hash 2': md5_hash2, 'Match': match})

            if not match:
                identical = False
                unmatched_files.append(filename)  # Log the unmatched file
                report[-1]['Error'] = 'MD5 hash mismatch'
        else:
            identical = False
            unmatched_files.append(filename)  # Log the missing file
            report.append({'Filename': filename, 'Error': 'Not found in second directory'})

    for filename in files_dir2.keys():
        if filename not in files_dir1:
            identical = False
            report.append({'Filename': filename, 'Error': 'Not found in first directory'})

    return report, identical, unmatched_files

def handle_file_conflict(target_dir, filename, md5_hash1, md5_hash2, md5_error_report):
    """Move existing file to the MD5 error folder if it conflicts with a new file."""
    md5_error_dir = os.path.join(target_dir, 'md5_errors')
    if not os.path.exists(md5_error_dir):
        os.makedirs(md5_error_dir)  # Create the MD5 error directory if it doesn't exist

    existing_file_path = os.path.join(target_dir, filename)
    if os.path.exists(existing_file_path):
        error_reason = f"MD5 hash mismatch: {md5_hash1} vs {md5_hash2}"
        shutil.move(existing_file_path, os.path.join(md5_error_dir, filename))
        md5_error_report.append({'Filename': filename, 'Reason': error_reason})
        print(f"Moved existing file to MD5 errors: {filename}")

def copy_unmatched_files(unmatched_files, source_dir, target_dir, md5_error_report):
    """Copy unmatched files to the target directory with conflict handling."""
    for filename in unmatched_files:
        src = os.path.join(source_dir, filename)
        if os.path.exists(src):
            if filename in os.listdir(target_dir):
                target_file_path = os.path.join(target_dir, filename)
                md5_hash_src = calculate_md5(src)
                md5_hash_target = calculate_md5(target_file_path)
                handle_file_conflict(target_dir, filename, md5_hash_src, md5_hash_target, md5_error_report)  # Handle conflicts before copying
            try:
                shutil.copy2(src, target_dir)
                print(f"Copied unmatched file to Alliance: {filename}")
            except Exception as e:
                print(f"Error copying {filename}: {e}")

def validate_filenames(target_dir, filename_error_dir, filename_error_report):
    """Validate filenames in the target directory."""
    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)

        if os.path.isfile(file_path):
            if not is_valid_filename(filename):
                shutil.move(file_path, os.path.join(filename_error_dir, filename))
                filename_error_report.append({'Filename': filename, 'Reason': 'Invalid filename format'})
                print(f"[INVALID FILENAME] Moved: {filename} to {filename_error_dir}")

def validate_corrupt_images(target_dir, corrupt_file_dir, corrupt_report):
    """Validate images for corruption in the target directory."""
    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)

        if os.path.isfile(file_path) and is_valid_file_type(filename):
            if is_image_corrupted(file_path):
                shutil.move(file_path, os.path.join(corrupt_file_dir, filename))
                corrupt_report.append({'Filename': filename, 'Reason': 'Corrupted or unreadable'})
                print(f"[CORRUPTED FILE] Moved: {filename} to {corrupt_file_dir}")

def main(target_dir):
    filename_error_dir = os.path.join(target_dir, 'filename_errors')
    corrupt_file_dir = os.path.join(target_dir, 'corrupt_files')
    
    # Create error directories if they don't exist
    os.makedirs(filename_error_dir, exist_ok=True)
    os.makedirs(corrupt_file_dir, exist_ok=True)

    corrupt_report = []
    filename_error_report = []

    print("Starting validation process...\n")

    # Validate filenames
    validate_filenames(target_dir, filename_error_dir, filename_error_report)

    # Validate corrupted images
    validate_corrupt_images(target_dir, corrupt_file_dir, corrupt_report)

    print("\nValidation process completed.")
    
    # Print the reports separately
    print("Filename Error Report:")
    for entry in filename_error_report:
        print(f"- {entry['Filename']} : {entry['Reason']}")

    print("Corruption Report:")
    for entry in corrupt_report:
        print(f"- {entry['Filename']} : {entry['Reason']}")
                            
def main():
    dir1 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Alliance"
    dir2 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Picturae"
    
    if not os.path.exists(dir1):
        print(f"Directory 1 does not exist: {dir1}")
        return
    if not os.path.exists(dir2):
        print(f"Directory 2 does not exist: {dir2}")
        return

    md5_error_report = []  # List to hold MD5 error report entries
    filename_error_report = []  # List to hold filename error report entries
    corrupt_report = []  # List to hold corrupt file report entries

    # First comparison
    report, identical, unmatched_files = compare_directories(dir1, dir2)

    # Copy unmatched files from dir1 to the Alliance directory
    copy_unmatched_files(unmatched_files, dir1, dir1, md5_error_report)

    # Copy unmatched files from dir2 to the Alliance directory and re-run the comparison
    unmatched_files_dir2 = [f for f in os.listdir(dir2) if f not in os.listdir(dir1)]
    copy_unmatched_files(unmatched_files_dir2, dir2, dir1, md5_error_report)

    # Re-run comparison to include unmatched files in dir2
    report, identical, _ = compare_directories(dir1, dir2)

    # Convert comparison report to DataFrame and save to CSV
    df = pd.DataFrame(report)
    df.to_csv('comparison_report.csv', index=False)

    # Save MD5 error report to CSV if there are any errors
    if md5_error_report:
        md5_error_df = pd.DataFrame(md5_error_report)
        md5_error_df.to_csv(os.path.join(dir1, 'md5_errors', 'md5_error_report.csv'), index=False)

    # Validate filenames and check for image corruption
    validate_filenames_and_corruptions(dir1, corrupt_report)

    # Save corrupt file report to CSV if there are any errors
    if corrupt_report:
        corrupt_df = pd.DataFrame(corrupt_report)
        corrupt_df.to_csv(os.path.join(dir1, 'corrupt_files', 'corrupt_file_report.csv'), index=False)

    # Save filename error report to CSV if there are any errors
    if filename_error_report:
        filename_error_df = pd.DataFrame(filename_error_report)
        filename_error_df.to_csv(os.path.join(dir1, 'filename_errors', 'filename_error_report.csv'), index=False)

    # Add summary information
    with open('comparison_report.csv', 'a') as f:
        f.write(f'\n\nDirectories are identical: {identical}\n')

    if df.empty:
        print("The report is empty. No matching files found.")
    else:
        print('Comparison report saved to comparison_report.csv')

    if md5_error_report:
        print('MD5 error report saved to md5_errors/md5_error_report.csv')

    if corrupt_report:
        print('Corrupt file report saved to corrupt_files/corrupt_file_report.csv')

if __name__ == '__main__':
    main()

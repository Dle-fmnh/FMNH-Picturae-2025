import os
import hashlib
import pandas as pd
import shutil

def calculate_md5(file_path):
    """Calculate the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def is_valid_file_type(filename):
    """Check if the file type is among the specified types."""
    valid_extensions = ('.jpg', '.dng', '.tif', '.tiff', '.cr2')
    return filename.lower().endswith(valid_extensions)

def compare_directories(dir1, dir2):
    """Compare image files in two directories."""
    report = []
    unmatched_files = []

    all_files_dir1 = os.listdir(dir1)
    all_files_dir2 = os.listdir(dir2)

    # Print all files for debugging
    print("All files in Directory 1:")
    print(all_files_dir1)
    
    print("All files in Directory 2:")
    print(all_files_dir2)

    files_dir1 = {f: os.path.join(dir1, f) for f in all_files_dir1 if is_valid_file_type(f)}
    files_dir2 = {f: os.path.join(dir2, f) for f in all_files_dir2 if is_valid_file_type(f)}

    # Debugging: Print the valid filenames found
    print("Valid files in Directory 1:")
    print(files_dir1.keys())

    print("Valid files in Directory 2:")
    print(files_dir2.keys())

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
        else:
            identical = False
            unmatched_files.append(filename)  # Log the missing file
            report.append({'Filename': filename, 'Error': 'Not found in second directory'})

    for filename in files_dir2.keys():
        if filename not in files_dir1:
            identical = False
            report.append({'Filename': filename, 'Error': 'Not found in first directory'})

    return report, identical, unmatched_files

def handle_file_conflict(target_dir, filename, md5_hash1, md5_hash2, error_report):
    """Move existing file to the errors folder if it conflicts with a new file."""
    error_dir = os.path.join(target_dir, 'errors')
    if not os.path.exists(error_dir):
        os.makedirs(error_dir)  # Create the errors directory if it doesn't exist

    existing_file_path = os.path.join(target_dir, filename)
    if os.path.exists(existing_file_path):
        error_reason = f"MD5 hash mismatch: {md5_hash1} vs {md5_hash2}"
        shutil.move(existing_file_path, os.path.join(error_dir, filename))
        error_report.append({'Filename': filename, 'Reason': error_reason})
        print(f"Moved existing file to errors: {filename}")

def copy_unmatched_files(unmatched_files, source_dir, target_dir, error_report):
    """Copy unmatched files to the target directory with conflict handling."""
    for filename in unmatched_files:
        src = os.path.join(source_dir, filename)
        if os.path.exists(src):
            if filename in os.listdir(target_dir):
                # Calculate the MD5 hash of the source file and the target file
                target_file_path = os.path.join(target_dir, filename)
                md5_hash_src = calculate_md5(src)
                md5_hash_target = calculate_md5(target_file_path)
                handle_file_conflict(target_dir, filename, md5_hash_src, md5_hash_target, error_report)  # Handle conflicts before copying
            try:
                shutil.copy2(src, target_dir)
                print(f"Copied unmatched file to Alliance: {filename}")
            except Exception as e:
                print(f"Error copying {filename}: {e}")

def main():
    dir1 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Alliance"
    dir2 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Picturae"
    
    if not os.path.exists(dir1):
        print(f"Directory 1 does not exist: {dir1}")
        return
    if not os.path.exists(dir2):
        print(f"Directory 2 does not exist: {dir2}")
        return

    error_report = []  # List to hold error report entries

    # First comparison
    report, identical, unmatched_files = compare_directories(dir1, dir2)

    # Copy unmatched files from dir1 to the Alliance directory
    copy_unmatched_files(unmatched_files, dir1, dir1, error_report)

    # Copy unmatched files from dir2 to the Alliance directory and re-run the comparison
    unmatched_files_dir2 = [f for f in os.listdir(dir2) if f not in os.listdir(dir1)]
    copy_unmatched_files(unmatched_files_dir2, dir2, dir1, error_report)

    # Re-run comparison to include unmatched files in dir2
    report, identical, _ = compare_directories(dir1, dir2)

    # Convert report to DataFrame and save to CSV
    df = pd.DataFrame(report)
    df.to_csv('comparison_report.csv', index=False)

    # Save error report to CSV if there are any errors
    if error_report:
        error_df = pd.DataFrame(error_report)
        error_df.to_csv('error_report.csv', index=False)

    # Add summary information
    with open('comparison_report.csv', 'a') as f:
        f.write(f'\n\nDirectories are identical: {identical}\n')

    if df.empty:
        print("The report is empty. No matching files found.")
    else:
        print('Comparison report saved to comparison_report.csv')

    if error_report:
        print('Error report saved to error_report.csv')

if __name__ == '__main__':
    main()

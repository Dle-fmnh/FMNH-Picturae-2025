import os
import re
import cv2
import hashlib
import numpy as np
import pandas as pd

# Function to validate file type (images)
def is_valid_file_type(filename):
    return filename.lower().endswith(('.jpg', '.jpeg', '.dng', '.cr2', '.tif', '.tiff'))

# Function to validate filename based on the pattern
def is_valid_filename(filename):
    pattern = r'^(V\d{7}F|C\d{7}F)\.(jpg|jpeg|dng|cr2|tif|tiff)$'
    return re.match(pattern, filename, re.IGNORECASE) is not None

# Function to check if the image is corrupted
def is_image_corrupted(file_path):
    image = cv2.imread(file_path)
    return image is None

# Function to compute MD5 hash of a file
def get_md5_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Function to compare files in two directories
def compare_directories(dir1, dir2):
    comparison_report = []
    identical = True
    dir1_files = {f: get_md5_hash(os.path.join(dir1, f)) for f in os.listdir(dir1) if is_valid_file_type(f)}
    dir2_files = {f: get_md5_hash(os.path.join(dir2, f)) for f in os.listdir(dir2) if is_valid_file_type(f)}

    # Compare files in dir1 against dir2
    for filename in dir1_files:
        if filename in dir2_files:
            md5_match = dir1_files[filename] == dir2_files[filename]
            comparison_report.append({'Filename': filename, 'MD5 Match': md5_match})
            if not md5_match:
                identical = False
        else:
            identical = False
            comparison_report.append({'Filename': filename, 'MD5 Match': False, 'Not Found In': 'Picturae'})

    # Compare files in dir2 against dir1
    for filename in dir2_files:
        if filename not in dir1_files:
            identical = False
            comparison_report.append({'Filename': filename, 'MD5 Match': False, 'Not Found In': 'Alliance'})

    # Add missing files to the combined report with a note
    for filename in dir1_files:
        if filename not in dir2_files:
            comparison_report.append({
                'Filename': filename,
                'MD5 Match': False,
                'Not Found In': 'Picturae',
                'White Balanced': None,
                'In Focus': None,
                'Uncorrupted': None,
                'Valid Filename': None
            })

    for filename in dir2_files:
        if filename not in dir1_files:
            comparison_report.append({
                'Filename': filename,
                'MD5 Match': False,
                'Not Found In': 'Alliance',
                'White Balanced': None,
                'In Focus': None,
                'Uncorrupted': None,
                'Valid Filename': None
            })

    return comparison_report, identical

# Function to validate files (check if valid filename and if file is corrupted)
def validate_files(target_dir, report):
    for filename in os.listdir(target_dir):
        if is_valid_file_type(filename):
            file_path = os.path.join(target_dir, filename)
            valid_filename = is_valid_filename(filename)
            corrupted = is_image_corrupted(file_path)

            # Always add the 'Uncorrupted' key, and ensure all other relevant keys are included
            report.append({
                'Filename': filename,
                'Valid Filename': valid_filename,
                'Uncorrupted': not corrupted,  # Reverse the value: True if not corrupted, False if corrupted
                'White Balanced': None,  # Placeholder for white balance
                'In Focus': None,        # Placeholder for focus
            })

# Function to check white balance of an image
def check_white_balance(image):
    img_float = image.astype(np.float32) / 255.0
    means = img_float.mean(axis=(0, 1))  # Calculate mean of RGB channels
    return means

# Function to check if the white balance is within a threshold
def is_white_balanced(means, threshold=0.1):
    return abs(means[0] - means[1]) < threshold and abs(means[1] - means[2]) < threshold

# Function to check focus of an image using Laplacian
def check_focus(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    focus_measure = cv2.Laplacian(gray, cv2.CV_64F).var()
    return focus_measure

# Function to check if the image is in focus
def is_in_focus(focus_measure, focus_threshold=100.0):
    return focus_measure > focus_threshold

# Function to process images and add results to the report
def process_images(folder_path, report):
    for entry in report:
        filename = entry['Filename']
        if is_valid_file_type(filename):
            file_path = os.path.join(folder_path, filename)
            image = cv2.imread(file_path)

            # Ensure the 'Uncorrupted' key exists
            if 'Uncorrupted' not in entry:
                print(f"Warning: 'Uncorrupted' key is missing for {filename}. Skipping file.")
                continue  # Skip if 'Uncorrupted' key is missing

            # Check if the image is uncorrupted
            if not entry['Uncorrupted']:  # We now check for Uncorrupted, which is True if the image is not corrupted
                entry['White Balanced'] = "Unable to open file"
                entry['In Focus'] = "Unable to open file"
                continue  # Skip further checks for this image

            # Check white balance
            white_balance = check_white_balance(image)
            white_balanced = is_white_balanced(white_balance)

            # Check focus
            focus = check_focus(image)
            in_focus = is_in_focus(focus)

            # Update report with white balance and focus checks
            entry['White Balanced'] = white_balanced
            entry['In Focus'] = in_focus

# Main function
def main():
    dir1 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Alliance\errors"
    dir2 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Picturae"

    if not os.path.exists(dir1):
        print(f"Directory 1 does not exist: {dir1}")
        return
    if not os.path.exists(dir2):
        print(f"Directory 2 does not exist: {dir2}")
        return

    report = []

    # Compare directories first
    comparison_report, identical = compare_directories(dir1, dir2)

    # Validate filenames and check for image corruption
    validate_files(dir1, report)

    # Process images for white balance and focus checks
    process_images(dir1, report)

    # Add comparison results to the report
    for entry in report:
        filename = entry['Filename']
        comparison_entry = next((comp for comp in comparison_report if comp['Filename'] == filename), None)
        if comparison_entry:
            entry['MD5 Match'] = comparison_entry.get('MD5 Match', None)

    # Save the combined report as a CSV directly in dir1
    report_df = pd.DataFrame(report)
    report_df.to_csv(os.path.join(dir1, 'analysis_report.csv'), index=False)

    # Save the comparison report separately if needed
    comparison_df = pd.DataFrame(comparison_report)
    comparison_df.to_csv('comparison_report_for_errors.csv', index=False)

    with open('comparison_report.csv', 'a') as f:
        f.write(f'\n\nDirectories are identical: {identical}\n')

    print('Reports generated.')

if __name__ == "__main__":
    main()

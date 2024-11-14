####  Major change in 2_2 is that it consolidates all errors into singular folder.
##  error csv contains most checks however, file will not undergo image qc if file name, md5, or corruption error is present
## discovered that error csv contains files that have no errors and comparison csv contains all files

# validates file type and moves errors
# validates file name and moves errors
# checks image corruption and moves errors
# checks and compares md5 hash and moves errors
# compares directories and moves what is missing (will need to amend for time stamps and not full directories)
# reports everything into csv files.  errors separated
# checks for white balance and focusing base on average rgb values and laplacian of image.
### White balance check should be modified so that gray is defined by a grey card on the specimen.
### Alternatively grey can be defined separately and compared among all images for uniformity and consistency



import os
import re
import cv2
import hashlib
import shutil
import numpy as np
import pandas as pd

def is_valid_file_type(filename):
    return filename.lower().endswith(('.jpg', '.jpeg', '.dng', '.cr2', '.tif', '.tiff'))

def is_valid_filename(filename):
    pattern = r'^(V\d{7}F|C\d{7}F)\.(jpg|jpeg|dng|cr2|tif|tiff)$'
    return re.match(pattern, filename, re.IGNORECASE) is not None

def is_image_corrupted(file_path):
    image = cv2.imread(file_path)
    return image is None

def get_md5_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compare_directories(dir1, dir2):
    report = []
    identical = True
    dir1_files = {f: get_md5_hash(os.path.join(dir1, f)) for f in os.listdir(dir1) if is_valid_file_type(f)}
    dir2_files = {f: get_md5_hash(os.path.join(dir2, f)) for f in os.listdir(dir2) if is_valid_file_type(f)}

    for filename in dir1_files:
        if filename in dir2_files:
            md5_match = dir1_files[filename] == dir2_files[filename]
            report.append({'Filename': filename, 'MD5 Match': md5_match})
            if not md5_match:
                identical = False
        else:
            identical = False
            report.append({'Filename': filename, 'MD5 Match': False, 'Not Found In': 'Picturae'})

    for filename in dir2_files:
        if filename not in dir1_files:
            identical = False
            report.append({'Filename': filename, 'MD5 Match': False, 'Not Found In': 'Alliance'})

    return report, identical

def validate_and_report_issues(target_dir, report):
    errors_dir = os.path.join(target_dir, 'errors')
    if not os.path.exists(errors_dir):
        os.makedirs(errors_dir)

    for filename in os.listdir(target_dir):
        if is_valid_file_type(filename):
            file_path = os.path.join(target_dir, filename)
            valid_filename = is_valid_filename(filename)
            corrupted = is_image_corrupted(file_path)

            if corrupted:
                report.append({'Filename': filename, 'Valid Filename': valid_filename, 'Corrupted': True, 'White Balanced': None, 'In Focus': None})
                shutil.move(file_path, os.path.join(errors_dir, filename))
            elif not valid_filename:
                report.append({'Filename': filename, 'Valid Filename': False, 'Corrupted': False, 'White Balanced': None, 'In Focus': None})
                shutil.move(file_path, os.path.join(errors_dir, filename))
            else:
                report.append({'Filename': filename, 'Valid Filename': True, 'Corrupted': False, 'White Balanced': None, 'In Focus': None})

def check_white_balance(image):
    img_float = image.astype(np.float32) / 255.0
    means = img_float.mean(axis=(0, 1))  # Calculate mean of RGB channels
    return means

def is_white_balanced(means, threshold=0.1):
    return abs(means[0] - means[1]) < threshold and abs(means[1] - means[2]) < threshold

def check_focus(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    focus_measure = cv2.Laplacian(gray, cv2.CV_64F).var()
    return focus_measure

def is_in_focus(focus_measure, focus_threshold=100.0):
    return focus_measure > focus_threshold

def process_images(folder_path, report):
    for entry in report:
        filename = entry['Filename']
        if entry['Valid Filename'] and not entry['Corrupted']:
            file_path = os.path.join(folder_path, filename)
            image = cv2.imread(file_path)

            if image is None:
                continue  # This case should have been handled already

            # Check white balance
            white_balance = check_white_balance(image)
            white_balanced = is_white_balanced(white_balance)

            # Check focus
            focus = check_focus(image)
            in_focus = is_in_focus(focus)

            # Update report with white balance and focus checks
            entry['White Balanced'] = white_balanced
            entry['In Focus'] = in_focus

            if not in_focus or not white_balanced:
                shutil.move(file_path, os.path.join(folder_path, 'errors', filename))

def main():
    dir1 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Alliance"
    dir2 = r"C:\Users\Danie\Pictures\For Work\pytests\test2\Picturae"

    if not os.path.exists(dir1):
        print(f"Directory 1 does not exist: {dir1}")
        return
    if not os.path.exists(dir2):
        print(f"Directory 2 does not exist: {dir2}")
        return

    report = []

    # First comparison
    comparison_report, identical = compare_directories(dir1, dir2)

    # Validate filenames and check for image corruption
    validate_and_report_issues(dir1, report)

    # Process images for white balance and focus checks
    process_images(dir1, report)

    # Combine all reports into a single report
    if report:
        report_df = pd.DataFrame(report)
        report_df.to_csv(os.path.join(dir1, 'errors', 'error_report.csv'), index=False)

    # Save the comparison report
    comparison_df = pd.DataFrame(comparison_report)
    comparison_df.to_csv('comparison_report.csv', index=False)

    with open('comparison_report.csv', 'a') as f:
        f.write(f'\n\nDirectories are identical: {identical}\n')

    print('Reports generated.')

if __name__ == "__main__":
    main()

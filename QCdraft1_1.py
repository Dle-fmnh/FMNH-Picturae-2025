###Incomplete and doesn't work as a first draft.

import os
import re
import cv2
import pandas as pd
import hashlib
import shutil

def is_valid_filename(filename):
    """Check if the filename matches the valid barcode format."""
    pattern = r'^(V\d{7}F|C\d{7}F)\.(jpg|jpeg|dng)$'
    return re.match(pattern, filename, re.IGNORECASE) is not None

def calculate_checksum(file_path):
    """Calculate the MD5 checksum of the file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def check_white_balance(image):
    """Calculate the average RGB values of the image."""
    img_float = image.astype(np.float32) / 255.0
    return img_float.mean(axis=(0, 1))

def is_white_balanced(means, threshold=0.1):
    """Check if the image is white balanced based on the average RGB values."""
    return abs(means[0] - means[1]) < threshold and abs(means[1] - means[2]) < threshold

def check_focus(image):
    """Calculate the focus measure of the image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def is_in_focus(focus_measure, focus_threshold=100.0):
    """Check if the image is in focus based on the focus measure."""
    return focus_measure > focus_threshold

def load_completed_barcodes(file_path):
    """Load processed barcodes from a text file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return set(f.read().strip().splitlines())
    return set()

def save_completed_barcodes(file_path, barcodes):
    """Save the set of completed barcodes to a text file."""
    with open(file_path, 'w') as f:
        for barcode in barcodes:
            f.write(f"{barcode}\n")

def load_barcode_list(file_path='valid_barcodes.txt'):
    """Load valid barcodes from a text file in the script's directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the script
    full_path = os.path.join(script_dir, file_path)  # Construct the full path
    if os.path.exists(full_path):
        with open(full_path, 'r') as f:
            return set(f.read().strip().splitlines())
    else:
        print(f"Warning: {full_path} not found. Returning an empty set.")
        return set()

def check_checksum_with_server(filename, checksum):
    """Placeholder function for checksum verification with the Picturae server."""
    # Implement actual server checking logic here
    return True  # For testing, assume all checksums are valid

def process_images(folder_path, completed_barcodes, barcode_list, error_folder):
    """Process images for QC checks and log results."""
    results = []
    errors = []

    # Create error folder if it doesn't exist
    os.makedirs(error_folder, exist_ok=True)

    for filename in os.listdir(folder_path):
        if not is_valid_filename(filename):
            errors.append((filename, "Invalid filename format"))
            continue
        
        file_path = os.path.join(folder_path, filename)
        checksum = calculate_checksum(file_path)

        # Check checksum with Picturae server
        if not check_checksum_with_server(filename, checksum):
            errors.append((filename, "Checksum mismatch"))
            continue
        
        barcode = filename.split('.')[0]  # Extract barcode from filename
        
        # Check if barcode already processed
        if barcode in completed_barcodes:
            # Move the file to the error folder and log the error
            shutil.move(file_path, os.path.join(error_folder, filename))
            errors.append((filename, "Barcode already processed - moved to error folder"))
            continue
        
        if barcode not in barcode_list:
            errors.append((filename, "Invalid barcode"))
            continue

        image = cv2.imread(file_path)
        if image is None:
            errors.append((filename, "Image could not be read"))
            continue

        # Check white balance
        white_balance = check_white_balance(image)
        if not is_white_balanced(white_balance):
            errors.append((filename, "Not white balanced"))
            continue

        # Check focus
        focus_measure = check_focus(image)
        if not is_in_focus(focus_measure):
            errors.append((filename, "Out of focus"))
            continue

        # If all checks pass, log the result
        results.append({
            'Barcode': barcode,
            'Date Created': os.path.getctime(file_path),
            'Checksum': checksum,
            'White Balanced': True,
            'In Focus': True
        })
        
        # Add barcode to completed list
        completed_barcodes.add(barcode)

    # Save results and errors to CSV
    if results:
        pd.DataFrame(results).to_csv(os.path.join(folder_path, 'import_ready.csv'), index=False)
    if errors:
        pd.DataFrame(errors, columns=['Filename', 'Error']).to_csv(os.path.join(folder_path, 'error_log.csv'), index=False)

    # Update the completed barcodes file
    save_completed_barcodes(os.path.join(folder_path, 'completed_barcodes.txt'), completed_barcodes)

if __name__ == "__main__":
    folder_path = input("Enter the folder path containing images: ")
    barcode_list = load_barcode_list()  # Now loads from the same directory as the script
    completed_barcodes = load_completed_barcodes(os.path.join(folder_path, 'completed_barcodes.txt'))
    error_folder = os.path.join(folder_path, 'error_files')  # Define the error folder
    process_images(folder_path, completed_barcodes, barcode_list, error_folder)
    print("QC process completed.")

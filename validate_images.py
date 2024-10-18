import os
import re
import cv2

def is_valid_filename(filename):
    # Define the regex patterns for the file names
    pattern = r'^(V\d{7}F|C\d{7}F)\.(jpg|jpeg|dng|cr2|tif|tiff)$'
    return re.match(pattern, filename, re.IGNORECASE) is not None

def is_image_corrupted(file_path):
    # Try to read the image and check if it is valid
    image = cv2.imread(file_path)
    return image is None

def process_images(folder_path):
    valid_files = []
    invalid_files = []

    for filename in os.listdir(folder_path):
        if is_valid_filename(filename):
            file_path = os.path.join(folder_path, filename)

            if is_image_corrupted(file_path):
                invalid_files.append((filename, "Corrupted or unreadable"))
            else:
                valid_files.append(filename)
        else:
            invalid_files.append((filename, "Invalid filename format"))

    # Display results
    if valid_files:
        print("Valid Files:")
        for valid_file in valid_files:
            print(valid_file)
    else:
        print("No valid files found.")

    if invalid_files:
        print("\nInvalid Files:")
        for invalid_file in invalid_files:
            print(f"{invalid_file[0]} - {invalid_file[1]}")
    else:
        print("No invalid files found.")

if __name__ == "__main__":
    folder_path = input("Enter the folder path containing images: ")
    process_images(folder_path)

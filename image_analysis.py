import os
import cv2
import numpy as np
import pandas as pd

def check_white_balance(image):
    img_float = image.astype(np.float32) / 255.0
    means = img_float.mean(axis=(0, 1))  # Calculate mean of RGB channels
    return means

def is_white_balanced(means, threshold=0.1):
    # Define a simple threshold for white balance
    return abs(means[0] - means[1]) < threshold and abs(means[1] - means[2]) < threshold

def check_focus(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    focus_measure = cv2.Laplacian(gray, cv2.CV_64F).var()
    return focus_measure

def is_in_focus(focus_measure, focus_threshold=100.0):
    return focus_measure > focus_threshold

def process_images(folder_path):
    results = []
    valid_extensions = ('.jpg', '.jpeg', '.tif', '.tiff', '.dng', '.cr2')

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(valid_extensions):
            file_path = os.path.join(folder_path, filename)
            image = cv2.imread(file_path)

            if image is None:
                print(f"Could not read image: {filename}")
                continue

            # Check white balance
            white_balance = check_white_balance(image)
            white_balanced = is_white_balanced(white_balance)

            # Check focus
            focus = check_focus(image)
            in_focus = is_in_focus(focus)

            # Append the results
            results.append({
                'Filename': filename,
                'White Balance (R,G,B)': white_balance,
                'Focus Measure': focus,
                'In Focus': in_focus,
                'White Balanced': white_balanced
            })

    # Create a DataFrame and save to CSV
    df = pd.DataFrame(results)
    df.to_csv(os.path.join(folder_path, 'image_analysis_results.csv'), index=False)

if __name__ == "__main__":
    folder_path = input("Enter the folder path containing images: ")
    process_images(folder_path)
    print("Image analysis completed and results saved to CSV.")

import os
import hashlib
import exifread
import pandas as pd

def calculate_md5(file_path):
    """Calculate the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_exif_data(image_path):
    """Extract EXIF data from an image file."""
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f, stop_tag='EXIF')
        return {tag: str(value) for tag, value in tags.items()}

def main(directory, output_csv):
    """Main function to generate a CSV report of image files and their MD5 hashes."""
    records = []

    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.tiff')):
            file_path = os.path.join(directory, filename)

            # Calculate MD5 hash
            md5_hash = calculate_md5(file_path)

            # Extract EXIF data
            exif_data = extract_exif_data(file_path)

            # Create record
            record = {
                'Filename': filename,
                'MD5 Hash': md5_hash,
                **exif_data  # Add EXIF data to the record
            }
            records.append(record)

    # Convert records to DataFrame
    df = pd.DataFrame(records)

    # Save to CSV
    df.to_csv(output_csv, index=False)
    print(f'Report saved to {output_csv}')

if __name__ == '__main__':
    directory_path = input("Enter the directory path containing images: ")
    output_csv_file = input("Enter the output CSV file name (e.g., report.csv): ")
    main(directory_path, output_csv_file)
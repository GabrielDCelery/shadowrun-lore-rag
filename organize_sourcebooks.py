#!/usr/bin/env python3
"""
Script to organize sourcebooks:
1. Match CSV entries to files in docs/SR
2. Create standardized copies in docs/copy
3. Update CSV with file names
"""

import csv
import os
import shutil
import re
from pathlib import Path

# Paths
CSV_PATH = Path("docs/sourcebooks.csv")
SR_DIR = Path("docs/SR")
COPY_DIR = Path("docs/copy")

def slugify(text):
    """Convert title to slug format"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def normalize_title(title):
    """Normalize title for matching"""
    # Remove common prefixes/suffixes and special characters
    title = title.lower()
    title = re.sub(r'^(the|shadowrun)\s+', '', title)
    title = re.sub(r'\s*\([^)]*\)', '', title)  # Remove parenthetical notes
    title = re.sub(r'[^\w\s]', '', title)  # Remove punctuation
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def find_matching_file(title, sr_files):
    """Find a matching file in SR directory"""
    normalized_title = normalize_title(title)
    title_words = set(normalized_title.split())

    best_match = None
    best_score = 0

    for filename in sr_files:
        # Extract the title part from filename (remove SKU prefix)
        file_title = re.sub(r'^[A-Z]+\d+[a-z]?\s*-\s*shadowrun\s*-\s*', '', filename, flags=re.IGNORECASE)
        file_title = file_title.replace('.pdf', '').replace('.PDF', '')
        normalized_file = normalize_title(file_title)
        file_words = set(normalized_file.split())

        # Calculate word overlap
        common_words = title_words & file_words
        if len(common_words) > 0:
            score = len(common_words) / max(len(title_words), len(file_words))
            if score > best_score and score > 0.4:  # Threshold for matching
                best_score = score
                best_match = filename

    return best_match

def main():
    # Create copy directory if it doesn't exist
    COPY_DIR.mkdir(exist_ok=True)

    # Get list of PDF files in SR directory
    sr_files = [f.name for f in SR_DIR.glob("*.pdf")] + [f.name for f in SR_DIR.glob("*.PDF")]

    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Process each row
    updates = []
    for row in rows:
        title = row['title']
        sku = row['sku'].split(',')[0].strip()  # Take first SKU if multiple
        current_filename = row.get('file_name', '').strip()

        # Skip if no SKU
        if not sku:
            updates.append(row)
            continue

        # Try to find matching file
        matched_file = find_matching_file(title, sr_files)

        if matched_file:
            # Generate standardized filename
            slug = slugify(title)
            new_filename = f"{sku}-{slug}.pdf"

            # Copy file
            src_path = SR_DIR / matched_file
            dst_path = COPY_DIR / new_filename

            print(f"✓ Matched: {title}")
            print(f"  Source: {matched_file}")
            print(f"  Target: {new_filename}")

            try:
                shutil.copy2(src_path, dst_path)
                row['owned'] = 'yes'
                row['file_name'] = new_filename
                print(f"  Copied successfully\n")
            except Exception as e:
                print(f"  Error copying: {e}\n")

        elif current_filename:
            # Keep existing filename
            print(f"- Keeping existing: {title} -> {current_filename}")
        else:
            print(f"✗ No match found: {title}")

        updates.append(row)

    # Write updated CSV
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['title', 'sku', 'isbn', 'publisher', 'owned', 'file_name']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updates)

    print("\n" + "="*60)
    print("CSV updated successfully!")

if __name__ == '__main__':
    main()

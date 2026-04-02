import os
import numpy as np
from PIL import Image
import argparse

def slice_image(image_path, output_dir, min_gap_height=10, variance_threshold=1.0, min_slice_height=500):
    """
    Slices a long vertical image into multiple parts based on horizontal gaps (uniform color rows).
    
    :param image_path: Path to the input image.
    :param output_dir: Directory to save the slices.
    :param min_gap_height: Minimum number of consecutive uniform rows to consider as a gap.
    :param variance_threshold: Maximum variance in a row to consider it "uniform".
    :param min_slice_height: Minimum height of a slice (to prevent too many small cuts).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Load image
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    img_array = np.array(img)

    print(f"Image loaded: {width}x{height}")

    # Calculate variance for each row
    # Variance of 0 means all pixels in the row are exactly the same color
    row_variances = np.var(img_array, axis=(1, 2))
    
    # Identify "gap" rows
    is_gap_row = row_variances <= variance_threshold
    
    # Find contiguous blocks of gap rows
    gap_points = []
    current_gap_start = -1
    
    for y in range(height):
        if is_gap_row[y]:
            if current_gap_start == -1:
                current_gap_start = y
        else:
            if current_gap_start != -1:
                gap_height = y - current_gap_start
                if gap_height >= min_gap_height:
                    # Add the middle of the gap as a potential slice point
                    gap_points.append(current_gap_start + gap_height // 2)
                current_gap_start = -1
    
    # Handle gap at the very end
    if current_gap_start != -1:
        gap_height = height - current_gap_start
        if gap_height >= min_gap_height:
            # We don't necessarily need to slice at the very bottom, but we record it
            pass

    # Determine final slice points (respecting min_slice_height)
    slice_indices = [0]
    last_slice_y = 0
    
    for gap_y in gap_points:
        if gap_y - last_slice_y >= min_slice_height:
            slice_indices.append(gap_y)
            last_slice_y = gap_y
            
    slice_indices.append(height)
    
    print(f"Found {len(slice_indices) - 1} slices.")

    # Perform slicing
    for i in range(len(slice_indices) - 1):
        top = slice_indices[i]
        bottom = slice_indices[i+1]
        
        # Crop and save
        slice_img = img.crop((0, top, width, bottom))
        output_filename = os.path.join(output_dir, f"slice_{i+1:02d}.png")
        slice_img.save(output_filename, "PNG")
        print(f"Saved: {output_filename} ({width}x{bottom-top})")

def process_path(input_path, output_base_dir, min_gap_height=10, variance_threshold=1.0, min_slice_height=500):
    """
    Handles both a single image file or a directory of images.
    """
    if os.path.isfile(input_path):
        # Single file
        # Use filename as subfolder in output directory
        filename = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.join(output_base_dir, filename)
        slice_image(input_path, output_dir, min_gap_height, variance_threshold, min_slice_height)
    elif os.path.isdir(input_path):
        # Directory
        print(f"Processing directory: {input_path}")
        for f in os.listdir(input_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                full_path = os.path.join(input_path, f)
                filename = os.path.splitext(f)[0]
                output_dir = os.path.join(output_base_dir, filename)
                slice_image(full_path, output_dir, min_gap_height, variance_threshold, min_slice_height)
    else:
        print(f"Error: {input_path} is not a valid file or directory.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Slice long vertical images into multiple parts.")
    parser.add_argument("input", help="Path to an image file or a directory containing images")
    parser.add_argument("--output", default="img/output", help="Base directory to save slices (default: img/output)")
    parser.add_argument("--gap", type=int, default=10, help="Minimum gap height in pixels (default: 10)")
    parser.add_argument("--var", type=float, default=1.0, help="Variance threshold for gap detection (default: 1.0)")
    parser.add_argument("--min_h", type=int, default=500, help="Minimum slice height in pixels (default: 500)")
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location if needed, 
    # but here we'll assume they are relative to CWD or absolute.
    process_path(args.input, args.output, min_gap_height=args.gap, variance_threshold=args.var, min_slice_height=args.min_h)

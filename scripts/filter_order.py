import os
import sys
import shutil

# Filtering where every nth image is preserved.
def filter_order(input_folder, filtered_folder, n=3):
    image_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])

    for i, filename in enumerate(image_files):
        if i % n == 0:
            src_path = os.path.join(input_folder, filename)
            dst_path = os.path.join(filtered_folder, filename)
            shutil.copy2(src_path, dst_path)

    print(f"Copied {len(range(0, len(image_files), n))} images.") 



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python3 filter_order.py <config_file>")
        sys.exit(1)

    # Setting basic parameters
    config_file = sys.argv[1]

    with open(config_file, 'r') as file:
        data = yaml.safe_load(file)

    n = data['step']

    # Setting up work folders
    input_folder = "/home/appuser/data/input_images"
    colmap_folder = "/home/appuser/data/colmap/"
    filtered_folder = "/home/appuser/data/colmap/images"

    shutil.rmtree(colmap_folder, ignore_errors=True)

    os.makedirs(filtered_folder, exist_ok=True)

    # Perform filtering by preserving every nth image
    filter_order(input_folder, filtered_folder, n)


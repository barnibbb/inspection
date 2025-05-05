import os
import yaml
from tqdm import tqdm
from PIL import Image
import imagehash
import shutil

# Perform image selection based on similarity.
# Only images that sufficiently differ from previous ones are preserved.
def filter_hash(input_folder, filtered_folder, similarity_threshold=0.03, hash_size=8):

    max_hamming_distance = int(hash_size * hash_size * similarity_threshold)

    hashes = []
    selected_files = []

    for filename in tqdm(sorted(os.listdir(input_folder))):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            filepath = os.path.join(input_folder, filename)

            try:
                img = Image.open(filepath)
                img_hash = imagehash.phash(img, hash_size=hash_size)
            except Excepion as e:
                print(f"Error processing {filename}: {e}")
                continue

            is_similar = any(existing_hash - img_hash <= max_hamming_distance for existing_hash in hashes)

            if not is_similar:
                hashes.append(img_hash)
                selected_files.append(filename)
                img.save(os.path.join(filtered_folder, filename))

    print(f"Selected {len(selected_files)} images out of {len(os.listdir(input_folder))}.")


if __name__ == "__main__":

    # Setting basic parameters
    config_file = "/home/appuser/data/config.yaml"

    with open(config_file, 'r') as file:
        data = yaml.safe_load(file)

    similarity_threshold = data['similarity_threshold']
    hash_size = data['hash_size']

    # Setting up work folders
    input_folder = "/home/appuser/data/input_images"
    colmap_folder = "/home/appuser/data/colmap"
    filtered_folder = "/home/appuser/data/colmap/images"

    shutil.rmtree(colmap_folder, ignore_errors=True)

    os.makedirs(filtered_folder, exist_ok=True)

    # Perform filtering by similarity
    filter_hash(input_folder, filtered_folder, similarity_threshold, hash_size)



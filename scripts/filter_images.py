import os
from tqdm import tqdm
from PIL import Image
import imagehash
import shutil

def filter_n(input_folder, filtered_folder, n=3):
    image_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])

    for i, filename in enumerate(image_files):
        if i % n == 0:
            src_path = os.path.join(input_folder, filename)
            dst_path = os.path.join(filtered_folder, filename)
            shutil.copy2(src_path, dst_path)

    print(f"Copied {len(range(0, len(image_files), n))} images.") 



def filter_hash(input_folder, filtered_folder):
    similarity_threshold = 0.03
    hash_size = 8
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

    input_folder = "/home/appuser/data/input_images"
    colmap_folder = "/home/appuser/data/colmap/"
    filtered_folder = "/home/appuser/data/colmap/images"

    shutil.rmtree(colmap_folder, ignore_errors=True)

    os.makedirs(filtered_folder, exist_ok=True)

    filter_n(input_folder, filtered_folder, 3)

    # filter_hash(input_folder, filtered_folder)



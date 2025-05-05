import subprocess
import time
import os
import shutil
import math
import yaml


def move_files(src_folder, dst_folder):
    shutil.copy2(src_folder + "cameras.bin", dst_folder + "cameras.bin")
    shutil.copy2(src_folder + "images.bin", dst_folder + "images.bin")
    shutil.copy2(src_folder + "points3D.bin", dst_folder + "points3D.bin")


if __name__ == "__main__":

    start_time = time.time()

    # Setup paths to directories
    work_folder = "/home/appuser/data/colmap/"
    database_path = work_folder + "aerial.db"
    image_path = work_folder + "images/"
    vocab_tree_path = work_folder + "../vocab_tree_flickr100K_words32K.bin"
    base_output_path = work_folder + "sparse/"
    output_model_path = base_output_path + "0/"
    dense_path = work_folder + "dense/"
    dense_text_path = work_folder + "dense_text/"
    ply_path = work_folder + "dense/fused.ply"

    input_path = work_folder + "input/"
    output_path = work_folder + "output/"
    output_base = work_folder + "sub/"

    # Initial cleanup
    shutil.rmtree(dense_path, ignore_errors=True)
    shutil.rmtree(dense_text_path, ignore_errors=True)
    shutil.rmtree(output_path, ignore_errors=True)
    shutil.rmtree(base_output_path, ignore_errors=True)
    shutil.rmtree(output_base, ignore_errors=True)
    shutil.rmtree(input_path, ignore_errors=True)

    if os.path.exists(database_path):
        result = subprocess.run(f"rm {database_path}", shell=True, check=True)

    # Creating required directories
    os.makedirs(base_output_path, exist_ok=True)
    os.makedirs(input_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(dense_path, exist_ok=True)
    os.makedirs(dense_text_path, exist_ok=True)


    # Reading basic parameters
    config_file = "/home/appuser/data/config.yaml"

    with open(config_file, 'r') as file:
        data = yaml.safe_load(file)


    # Splitting the input images to n subgroups
    n = data['image_groups']

    print(f"Number of image groups: {n}")

    for i in range(1, n+1):
        os.makedirs(os.path.join(output_base, str(i)), exist_ok=True)

    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')
    images = [f for f in os.listdir(image_path) if f.lower().endswith(image_extensions)]
    images.sort()

    chunk_size = math.ceil(len(images) / n)
    for i in range(n):
        chunk = images[i * chunk_size:(i+1) * chunk_size]
        dest_folder = os.path.join(output_base, str(i+1))
        for filename in chunk:
            src_path = os.path.join(image_path, filename)
            dst_path = os.path.join(dest_folder, filename)
            shutil.move(src_path, dst_path)


    # Incremental reconstruction with image groups
    images_before = set(os.listdir(image_path))

    for i in range(1, n+1):
        
        # Copying new images, simulating the upload of new images
        img_group_folder = f"{work_folder}/sub/{i}/"

        for filename in os.listdir(img_group_folder):
            filepath = os.path.join(img_group_folder, filename)

            extension = os.path.splitext(filename)[1].lower()

            if extension not in ('.jpg', '.jpeg', '.png'):
                continue

            destination = os.path.join(image_path, filename)

            shutil.copy2(filepath, destination)

        # Check for new images in the folder
        current_images = set(os.listdir(image_path))

        new_images = sorted(list(current_images - images_before))

        # Generating image_list.txt file from the new images
        image_list_path = f"{work_folder}/image_list.txt"

        with open(image_list_path, "w") as f:
            for name in new_images:
                f.write(name + '\n')

        images_before = set(os.listdir(image_path))

        # Feature extraction
        extractor = [
            "colmap", "feature_extractor",
            "--database_path", database_path,
            "--image_path", image_path,
            "--image_list_path", image_list_path,
            "--SiftExtraction.use_gpu", "1",
            "--ImageReader.camera_model", "FULL_OPENCV",
            "--ImageReader.camera_params", f"\"{data['fx']:.4f}, {data['fy']:.4f}, {data['cx']:.4f}, {data['cy']:.4f}, {data['k1']:.4f}, {data['k2']:.4f}, {data['p1']:.4f}, {data['p2']:.4f}, {data['k3']:.4f}, {data['k4']:.4f}, {data['k5']:.4f}, {data['k6']:.4f}\""
            "--ImageReader.single_camera", "1"
        ]

        command_extractor = " ".join(extractor)
        result = subprocess.run(command_extractor, shell=True, check=True)


        # Feature matching
        # For this type of incremental reconstruction only vocab tree matching works
        matcher = [
            "colmap", "vocab_tree_matcher",
            "--database_path", database_path,
            "--VocabTreeMatching.vocab_tree_path", vocab_tree_path,
            "--VocabTreeMatching.match_list_path", image_list_path
        ]

        command_matcher = " ".join(matcher)
        result = subprocess.run(command_matcher, shell=True, check=True)


        # 3D mapping
        if i == 1:
            src_folder = output_model_path
            out_path = base_output_path
        else:
            src_folder = output_path
            out_path = output_path

        mapper = [
            "colmap", "mapper",
            "--database_path", database_path,
            "--image_path", image_path,
            "--output_path", out_path,
            "--Mapper.multiple_models", "0",
            "--Mapper.ba_refine_focal_length", "0",
            "--Mapper.ba_refine_extra_params", "0"
        ]

        # In the first iteration no input reconstruction is set
        if i > 1:
            mapper.append("--input_path")
            mapper.append(input_path)

        command_mapper = " ".join(mapper)
        result = subprocess.run(command_mapper, shell=True, check=True)
        
        # Moving output files to the input folder, for the next iteration
        move_files(src_folder, input_path)

        # Moving output files in first iteration for visualization
        if i == 1:
            move_files(output_model_path, output_path)


    # Image undistortion
    undistort = [
        "colmap", "image_undistorter", 
        "--input_path", input_path, 
        "--image_path", image_path, 
        "--output_path", dense_path]

    command_undistort = " ".join(undistort)
    result = subprocess.run(command_undistort, shell=True, check=True)


    # Stereo matching
    stereo = [
        "colmap", "patch_match_stereo", 
        "--workspace_path", dense_path, 
        "--PatchMatchStereo.num_iterations", f"{data['num_iterations']}",
        "--PatchMatchStereo.geom_consistency", f"{data['geom_consistency']}",
        "--PatchMatchStereo.filter", f"{data['filter']}",
        "--PatchMatchStereo.max_image_size", f"{data['max_image_size']}",
        "--PatchMatchStereo.window_step", f"{data['window_step']}",
        "--PatchMatchStereo.window_radius", f"{data['window_radius']}",
        "--PatchMatchStereo.num_samples", f"{data['num_samples']}"]

    command_stereo = " ".join(stereo)
    result = subprocess.run(command_stereo, shell=True, check=True)


    # Stereo fusion
    fusion = [
        "colmap", "stereo_fusion",
        "--workspace_path", dense_path,
        "--workspace_format", "COLMAP",
        "--input_type", "photometric",
        "--output_path", dense_text_path,
        "--output_type", "TXT",
        "--StereoFusion.min_num_pixels", "3"]

    command_fusion = " ".join(fusion)
    result = subprocess.run(command_fusion, shell=True, check=True)


    # Dense export
    export = [
        "colmap", "model_converter",
        "--input_path", dense_text_path,
        "--output_path", ply_path,
        "--output_type", "PLY"]

    command_export = " ".join(export)
    result = subprocess.run(command_export, shell=True, check=True)


    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Execution time:\t {execution_time} seconds.")

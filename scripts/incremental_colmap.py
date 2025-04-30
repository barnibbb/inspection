import subprocess
import time
import os
import sys
import shutil
import math


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python3 incremental_colmap.py <work_folder_path>")
        sys.exit(1)

    work_folder = sys.argv[1]

    database_path = work_folder + "/aerial.db"
    image_path = work_folder + "/images/"
    vocab_tree_path = work_folder + "../vocab_tree_flickr100K_words32K.bin"
    base_output_path = work_folder + "/sparse/"
    output_model_path = base_output_path + "/0/"
    dense_path = work_folder + "/dense/"
    dense_text_path = work_folder + "/dense_text/"
    ply_path = work_folder + "/dense/fused.ply"

    input_path = work_folder + "/input/"
    output_path = work_folder + "/output/"
    output_base = work_folder + "/sub/"

    # Initial cleanup
    shutil.rmtree(dense_path, ignore_errors=True)
    shutil.rmtree(dense_text_path, ignore_errors=True)
    shutil.rmtree(output_path, ignore_errors=True)
    shutil.rmtree(base_output_path, ignore_errors=True)
    shutil.rmtree(output_base, ignore_errors=True)
    shutil.rmtree(input_path, ignore_errors=True)

    if os.path.exists(database_path):
        result = subprocess.run(f"rm {database_path}", shell=True, check=True)


    

    os.makedirs(base_output_path, exist_ok=True)
    os.makedirs(input_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(dense_path, exist_ok=True)
    os.makedirs(dense_text_path, exist_ok=True)



    # Splitting the input images to n subgroups
    n = 7

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


    images_before = set(os.listdir(image_path))

    # Incremental reconstruction with image groups
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
            "--ImageReader.camera_model", "PINHOLE",
            "--ImageReader.camera_params", "\"1064.27, 1064.27, 986.697, 559.228\"",
            # "--ImageReader.camera_model", "FULL_OPENCV",
            # "--ImageReader.camera_params", "\"3774.87519624938522611046, 3774.87519624938522611046, 2994.32053596355581248645, 2009.16854628427108764299, -0.07513844017734828962, 0.07885532382347501534, 0.00030047767052433631, -0.00002012382737918220, -0.02505007537309405716, 0, 0, 0\"",
            "--ImageReader.single_camera", "1"
        ]

        command_extractor = " ".join(extractor)

        result = subprocess.run(command_extractor, shell=True, check=True)


        # Feature matching
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
            mapper = [
                "colmap", "mapper",
                "--database_path", database_path,
                "--image_path", image_path,
                "--output_path", base_output_path,
                "--Mapper.multiple_models", "0",
                "--Mapper.ba_refine_focal_length", "0",
                "--Mapper.ba_refine_extra_params", "0"
            ]

            cameras_1 = output_model_path + "cameras.bin"
            images_1 = output_model_path + "images.bin"
            points_1 = output_model_path + "points3D.bin"

            cameras_2 = input_path + "cameras.bin"
            images_2 = input_path + "images.bin"
            points_2 = input_path + "points3D.bin"


        else:
            mapper = [
                "colmap", "mapper",
                "--database_path", database_path,
                "--image_path", image_path,
                "--input_path", input_path,
                "--output_path", output_path,
                "--Mapper.multiple_models", "0",
                "--Mapper.ba_refine_focal_length", "0",
                "--Mapper.ba_refine_extra_params", "0"
            ]

            cameras_1 = output_path + "cameras.bin"
            images_1 = output_path + "images.bin"
            points_1 = output_path + "points3D.bin"

            cameras_2 = input_path +  "cameras.bin"
            images_2 = input_path + "images.bin"
            points_2 = input_path + "points3D.bin"


        command_mapper = " ".join(mapper)

        result = subprocess.run(command_mapper, shell=True, check=True)
        
        shutil.copy2(cameras_1, cameras_2)
        shutil.copy2(images_1, images_2)
        shutil.copy2(points_1, points_2)

        if i == 1:
            cameras_3 = output_path + "cameras.bin"
            images_3 = output_path + "images.bin"
            points_3 = output_path + "points3D.bin"

            shutil.copy2(cameras_1, cameras_3)
            shutil.copy2(images_1, images_3)
            shutil.copy2(points_1, points_3)


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
        "--PatchMatchStereo.num_iterations", "3",
        "--PatchMatchStereo.geom_consistency", "0",
        "--PatchMatchStereo.filter", "1",
        "--PatchMatchStereo.max_image_size", "1000",
        "--PatchMatchStereo.window_step", "2",
        "--PatchMatchStereo.window_radius", "3",
        "--PatchMatchStereo.num_samples", "10"]

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






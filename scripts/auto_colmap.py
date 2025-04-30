import subprocess
import time
import os


work_folder = "/home/appuser/data/colmap"

database_path = work_folder + "/aerial.db"
image_path = work_folder + "/images/"
output_path = work_folder + "/sparse/"
input_path = work_folder + "/sparse/0/"
dense_path = work_folder + "/dense/"
dense_text_path = work_folder + "/dense_text/"
ply_path = work_folder + "/dense/fused.ply"

os.makedirs(output_path, exist_ok=True)
os.makedirs(dense_path, exist_ok=True)
os.makedirs(dense_text_path, exist_ok=True)

extraction = [
    "colmap", "feature_extractor",
    "--database_path", database_path,
    "--image_path", image_path,
    "--ImageReader.camera_model", "PINHOLE",
    "--ImageReader.camera_params", "\"1064.27, 1064.27, 986.697, 559.228\"",
    "--ImageReader.single_camera", "1"]


command_extraction = " ".join(extraction)

matcher = [
    "colmap", "exhaustive_matcher", 
    "--database_path", database_path]

command_matcher = " ".join(matcher)

sparse = [
    "colmap", "mapper",
    "--database_path", database_path,
    "--image_path", image_path,
    "--output_path", output_path,
    "--Mapper.multiple_models", "0",
    "--Mapper.ba_refine_focal_length", "0",
    "--Mapper.ba_refine_extra_params", "0"]

command_sparse = " ".join(sparse)

undistort = [
    "colmap", "image_undistorter", 
    "--input_path", input_path, 
    "--image_path", image_path, 
    "--output_path", dense_path]

command_undistort = " ".join(undistort)

stereo = [
    "colmap", "patch_match_stereo", 
    "--workspace_path", dense_path, 
    "--PatchMatchStereo.num_iterations", "1",
    "--PatchMatchStereo.geom_consistency", "0",
    "--PatchMatchStereo.filter", "1",
    "--PatchMatchStereo.max_image_size", "1000",
    "--PatchMatchStereo.window_step", "2",
    "--PatchMatchStereo.window_radius", "3",
    "--PatchMatchStereo.num_samples", "10"]

command_stereo = " ".join(stereo)

fusion = [
    "colmap", "stereo_fusion",
    "--workspace_path", dense_path,
    "--workspace_format", "COLMAP",
    "--input_type", "photometric",
    "--output_path", dense_text_path,
    "--output_type", "TXT",
    "--StereoFusion.min_num_pixels", "3"]

command_fusion = " ".join(fusion)

export = [
    "colmap", "model_converter",
    "--input_path", dense_text_path,
    "--output_path", ply_path,
    "--output_type", "PLY"]

command_export = " ".join(export)

start_time = time.time()
result = subprocess.run(command_extraction, shell=True, check=True)
end_time = time.time()
execution_time1 = end_time - start_time


start_time = time.time()
result = subprocess.run(command_matcher, shell=True, check=True)
end_time = time.time()
execution_time2 = end_time - start_time


start_time = time.time()
result = subprocess.run(command_sparse, shell=True, check=True)
end_time = time.time()
execution_time3 = end_time - start_time


start_time = time.time()
result = subprocess.run(command_undistort, shell=True, check=True)
end_time = time.time()
execution_time4 = end_time - start_time


start_time = time.time()
result = subprocess.run(command_stereo, shell=True, check=True)
end_time = time.time()
execution_time5 = end_time - start_time


start_time = time.time()
result = subprocess.run(command_fusion, shell=True, check=True)
end_time = time.time()
execution_time6 = end_time - start_time


result = subprocess.run(command_export, shell=True, check=True)

print(f"Execution time feature extraction:\t {execution_time1} seconds.")
print(f"Execution time feature matching:\t {execution_time2} seconds.")
print(f"Execution time sparse reconstruction:\t {execution_time3} seconds.")
print(f"Execution time image undistortion:\t {execution_time4} seconds.")
print(f"Execution time stereo matching:\t\t {execution_time5} seconds.")
print(f"Execution time stereo fusion:\t\t {execution_time6} seconds.")

print(f"Execution time full process:\t\t {execution_time1+execution_time2+execution_time3+execution_time4+execution_time5+execution_time6} seconds.")


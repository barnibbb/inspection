import os
import sys
import yaml

import numpy as np
import open3d as o3d

sys.path.append('/home/appuser/colmap/scripts/python')
from read_write_model import read_points3D_binary, read_images_binary, read_points3D_text


def read_points(points_path, sparse=True):
    # Reading 3D points
    if sparse:
        points3D = read_points3D_binary(points_path)
    else:
        points3D = read_points3D_text(points_path)

    pts = np.array([p.xyz for p in points3D.values()])
    colors = np.array([p.rgb / 255.0 for p in points3D.values()])

    pc = o3d.geometry.PointCloud()
    pc.points = o3d.utility.Vector3dVector(pts)
    pc.colors = o3d.utility.Vector3dVector(colors)

    # Outlier removal
    if sparse:
        pcd_clean, ind = pc.remove_statistical_outlier(nb_neighbors=data['s_nb_neighbors'], std_ratio=data['s_std_ratio'])
    else:
        pcd_clean, ind = pc.remove_statistical_outlier(nb_neighbors=data['d_nb_neighbors'], std_ratio=data['d_std_ratio'])

    return pcd_clean




if __name__ == '__main__':
    # Reading basic parameters
    config_file = "/home/appuser/data/config.yaml"

    with open(config_file, "r") as file:
        data = yaml.safe_load(file)

    # Setup paths
    sparse_dir = "/home/appuser/data/colmap/output"
    dense_dir = "/home/appuser/data/colmap/dense_text"

    points_path = os.path.join(sparse_dir, "points3D.bin")
    images_path = os.path.join(sparse_dir, "images.bin")
    dense_points_path = os.path.join(dense_dir, "points3D.txt")

    pcd_clean = read_points(dense_points_path, sparse=False)

    images = read_images_binary(images_path)

    camera_poses = []

    # Reading camera poses and converting to world coordinates
    for img in images.values():
        q = img.qvec
        t = img.tvec
        R = o3d.geometry.get_rotation_matrix_from_quaternion([q[0], q[1], q[2], q[3]])
        C = -R.T @ t
        camera_poses.append(C)

    center = np.mean(camera_poses, axis=0)


    extent = 5.0
    half_extent = np.array([extent / 2] * 3)

    bbox = o3d.geometry.AxisAlignedBoundingBox(
        min_bound=center-half_extent,
        max_bound=center+half_extent
    )

    pcd_cropped = pcd_clean.crop(bbox)

    cropped_ply = "/home/appuser/data/colmap/dense/cropped.ply"
    o3d.io.write_point_cloud(cropped_ply, pcd_cropped, write_ascii=False)

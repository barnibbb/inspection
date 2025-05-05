import os
import time
import yaml
import sys
import open3d as o3d
import numpy as np
import tkinter as tk

sys.path.append('/home/appuser/colmap/scripts/python')
from read_write_model import read_points3D_binary, read_images_binary, read_points3D_text


# Instead of simple spheres, frustum could be used for camera visualization
def create_frustum(R, C, R_x, scale=0.1):
    z = scale
    half_size = scale * 0.5
    pts_cam = np.array([
        [0, 0, 0],
        [-half_size, -half_size, z],
        [ half_size, -half_size, z],
        [ half_size,  half_size, z],
        [-half_size,  half_size, z]
    ])

    pts_world = (R.T @ pts_cam.T).T + C

    pts_world = (R_x @ pts_world.T).T

    lines = [
        [0, 1], [0, 2], [0, 3], [0, 4],
        [1, 2], [2, 3], [3, 4], [4, 1]
    ]

    colors = [[1, 0, 0] for _ in lines]
    line_set = o3d.geometry.LineSet(
        points=o3d.utility.Vector3dVector(pts_world),
        lines=o3d.utility.Vector2iVector(lines)
    )

    line_set.colors = o3d.utility.Vector3dVector(colors)

    return line_set


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


    pcd_clean.rotate(R_x, center=(0, 0, 0))

    return pcd_clean


def add_elements(vis, pcd, cameras, geom_added):
    if geom_added:
        vis.clear_geometries()
    
    vis.add_geometry(pcd)
    for s in cameras:
        vis.add_geometry(s)

    return vis





if __name__ == "__main__":

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
    
    # Waiting until the first 3D reconstruction is performed
    while True:
        if os.path.exists(points_path) and os.path.exists(images_path):
            break
        else:
            print("Waiting for colmap files to be created...")
        time.sleep(data['initial_check_interval'])

    # Setting up window for visualization
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy() 

    vis = o3d.visualization.Visualizer()
    vis.create_window("COLMAP Live Viewer", width=screen_width, height=screen_height)
    geom_added = False
    frustum = data.get('frustum', False)


    # Change orientation if required
    flip_orientation = data.get('flip_orientation', False)

    if flip_orientation == 1:
        R_x = np.array([
            [1,  0,  0],
            [0, -1,  0],
            [0,  0, -1]
        ])
    else:
        R_x = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ])


    while True:
        try:
            # Reading 3D points
            pcd_clean = read_points(points_path, True)

            # Reading camera poses
            images = read_images_binary(images_path)

            camera_poses = []

            # Reading camera poses and converting to world coordinates
            for img in images.values():
                q = img.qvec
                t = img.tvec
                R = o3d.geometry.get_rotation_matrix_from_quaternion([q[0], q[1], q[2], q[3]])
                C = -R.T @ t
                if frustum:
                    frustum = create_frustum(R, C, R_x)
                    camera_poses.append(frustum)
                else:
                    camera_poses.append(R_x @ C)
                
            if frustum:
                cameras = camera_poses
            else:
                cameras = [o3d.geometry.TriangleMesh.create_sphere(radius=0.05).translate(c) for c in camera_poses]

            for s in cameras:
                s.paint_uniform_color([1, 0, 0])

            # Add elements to visualization tool
            vis = add_elements(vis, pcd_clean, cameras, geom_added)
            geom_added = True
            
            vis.poll_events()
            vis.update_renderer()

        except Exception as e:
            print(f"Failed to read or update view: {e}")

        # When the dense reconstruction is created the loop is broken
        if os.path.exists(dense_points_path):
            break
        else:
            time.sleep(data['refresh_interval'])


    # Reading 3D points
    pcd_clean = read_points(dense_points_path, False)

    # Add elements to visualization tool
    vis = add_elements(vis, pcd_clean, cameras, geom_added)
    
    render_option = vis.get_render_option()
    render_option.point_size = 0.5

    vis.run()


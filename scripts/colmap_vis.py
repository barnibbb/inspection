import os
import time
import open3d as o3d
import numpy as np
import tkinter as tk

from read_write_model import read_points3D_binary, read_images_binary, read_points3D_text



def create_frustum(R, C, scale=0.5):
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




if __name__ == "__main__":

    sparse_dir = "/home/appuser/data/colmap/output/"
    dense_dir = "/home/appuser/data/colmap/dense_text"

    points_path = os.path.join(sparse_dir, "points3D.bin")
    images_path = os.path.join(sparse_dir, "images.bin")

    dense_points_path = os.path.join(dense_dir, "points3D.txt")

    filtered_ply = "/home/appuser/data/colmap/dense/filtered.ply"

    creation_check_time = 1

    while True:
        if os.path.exists(points_path) and os.path.exists(images_path):
            break
        else:
            print("Waiting for colmap files to be created...")
        time.sleep(creation_check_time)


    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy() 

    refresh_interval = 1

    vis = o3d.visualization.Visualizer()
    vis.create_window("COLMAP Live Viewer", width=screen_width, height=screen_height)
    geom_added = False

    R_x = np.array([
        [1,  0,  0],
        [0, -1,  0],
        [0,  0, -1]
    ])


    while True:
        try:
            points3D = read_points3D_binary(points_path)
            images = read_images_binary(images_path)

            pts = np.array([p.xyz for p in points3D.values()])
            colors = np.array([p.rgb / 255.0 for p in points3D.values()])

            cam_centers = []

            for img in images.values():
                q = img.qvec
                t = img.tvec
                R = o3d.geometry.get_rotation_matrix_from_quaternion([q[0], q[1], q[2], q[3]])
                C = -R.T @ t
                C = R_x @ C
                cam_centers.append(C)
                # frustum = create_frustum(R, C)
                # cam_frustums.append(frustum)

            pc = o3d.geometry.PointCloud()
            pc.points = o3d.utility.Vector3dVector(pts)
            pc.colors = o3d.utility.Vector3dVector(colors)

            pcd_clean, ind = pc.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)



            pcd_clean.rotate(R_x, center=(0, 0, 0))

            cam_spheres = [o3d.geometry.TriangleMesh.create_sphere(radius=0.1).translate(c) for c in cam_centers]

            for s in cam_spheres:
                s.paint_uniform_color([1, 0, 0])

            if not geom_added:
                vis.add_geometry(pcd_clean)
                for s in cam_spheres:
                    vis.add_geometry(s)
                geom_added = True
            else:
                vis.clear_geometries()
                vis.add_geometry(pcd_clean)
                for s in cam_spheres:
                    vis.add_geometry(s)
            
            vis.poll_events()
            vis.update_renderer()

        except Exception as e:
            print(f"Failed to read or update view: {e}")


        if os.path.exists(dense_points_path):
            break
        else:
            time.sleep(refresh_interval)


    points3D = read_points3D_text(dense_points_path)

    pts = np.array([p.xyz for p in points3D.values()])
    colors = np.array([p.rgb / 255.0 for p in points3D.values()])

    pc = o3d.geometry.PointCloud()
    pc.points = o3d.utility.Vector3dVector(pts)
    pc.colors = o3d.utility.Vector3dVector(colors)

    pcd_clean, ind = pc.remove_statistical_outlier(nb_neighbors=50, std_ratio=0.0001)

    pcd_clean.rotate(R_x, center=(0, 0, 0))

    cam_spheres = [o3d.geometry.TriangleMesh.create_sphere(radius=0.05).translate(c) for c in cam_centers]

    for s in cam_spheres:
        s.paint_uniform_color([1, 0, 0])

    if not geom_added:
        vis.add_geometry(pcd_clean)
        for s in cam_spheres:
            vis.add_geometry(s)
        geom_added = True
    else:
        vis.clear_geometries()
        vis.add_geometry(pcd_clean)
        for s in cam_spheres:
            vis.add_geometry(s)
    
    render_option = vis.get_render_option()
    render_option.point_size = 0.5

    vis.run()


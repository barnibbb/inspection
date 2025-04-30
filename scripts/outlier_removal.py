import open3d as o3d


if __name__ == "__main__":

    input_ply = "/home/appuser/data/colmap/dense/fused.ply"
    filtered_ply = "/home/appuser/data/colmap/dense/filtered.ply"

    pcd = o3d.io.read_point_cloud(input_ply)
    print(f"Original point cloud has {len(pcd.points)} points.")

    pcd_clean, ind = pcd.remove_statistical_outlier(nb_neighbors=50, std_ratio=0.0001)
    print(f"Filtered point cloud has {len(pcd_clean.points)} points.")

    o3d.io.write_point_cloud(filtered_ply, pcd_clean, write_ascii=False)


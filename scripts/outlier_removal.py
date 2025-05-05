import yaml
import open3d as o3d

if __name__ == "__main__":

    # Setup up paths
    input_ply = "/home/appuser/data/colmap/dense/fused.ply"
    filtered_ply = "/home/appuser/data/colmap/dense/filtered.ply"

    # Reading basic parameters
    config_file = "/home/appuser/data/config.yaml"

    with open(config_file, 'r') as file:
        data = yaml.safe_load(file)

    pcd = o3d.io.read_point_cloud(input_ply)
    print(f"Original point cloud has {len(pcd.points)} points.")

    pcd_clean, ind = pcd.remove_statistical_outlier(nb_neighbors=data['d_nb_neighbors'], std_ratio=data['d_std_ratio'])
    print(f"Filtered point cloud has {len(pcd_clean.points)} points.")

    o3d.io.write_point_cloud(filtered_ply, pcd_clean, write_ascii=False)


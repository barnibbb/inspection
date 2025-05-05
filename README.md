# Inspection

## Setup

```bash
./build_docker.sh
./run_docker.sh
```

The mounted data folder should look like this:

```text
data/
├── input_images/
├── config.yaml
└── vocab_tree_flickr100K_words32K.bin
```

The vocab_tree_flickr100K_words32K.bin and an example config.yaml files are provided.

## Preliminary filtering

Selecting images from the original folder. Based on current experience, the order-based filtering is preferred.

```bash
python3 filter_order.py
python3 filter_hash.py
```

## Incremental reconstruction

Running incremental reconstruction in colmap. In each iteration sparse reconstruction is performed with the newly added images.

```bash
python3 incremental_colmap.py
```

## Visualization

Should be run in parallel with the reconstruction to visualize the current state.

```bash
python3 colmap_vis.py
```

Example reconstruction of waste after filtering.

![Colmap visualization](/assets/colmap_vis.png "Colmap visualization")

## Outlier removal

Outliers can be removed not just during the visualization.

```bash
python3 outlier_removal.py
```

## Future work

- parameter test

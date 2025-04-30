# Inspection

## Preliminary filtering

Selecting every nth image from original folder.

```bash
python3 filter_images.py
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

## TODO

<ul>
    <li>Set parameter file, and yaml reading</li>
    <li>Update commands with arguments</li>
    <li>Test dataset path and usage</li>
</ul>

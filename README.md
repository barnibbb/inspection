# Inspection

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

## TODO

- Set parameter file, and yaml reading
- Update commands with arguments
- Test dataset path and usage

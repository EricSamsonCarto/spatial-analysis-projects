# spatial-analysis-projects

Quick spatial analysis projects, mostly in Jupyter notebooks.

## Structure

```
src/
├── core/
│   ├── config.py          # shared settings (empty for now)
│   └── spatial_ops.py     # geometry helpers: validate, simplify, fill small holes, dedupe, export
├── data/
│   ├── input_data/        # raw source files
│   └── output_data/       # files the notebooks write
├── notebooks/
│   ├── template.ipynb     # starting point for a new project
│   └── *.ipynb            # one notebook per project
└── requirements.txt
```

Notebooks add `src/` to the path so they can import from `core`.

## Projects

### Denver buildings PMTiles

[denver_buildings_pmtiles.ipynb](src/notebooks/denver_buildings_pmtiles.ipynb)

Takes the Colorado building footprints GeoJSON, drops duplicates, simplifies the shapes, removes small holes and fixes invalid geometry, then writes a PMTiles file for zoom levels 8 to 12.

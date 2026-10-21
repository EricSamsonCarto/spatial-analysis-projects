import os
import geopandas as gpd

from shapely.geometry import Polygon, MultiPolygon


def make_gdf_valid(gdf):
    """
    Ensure all geometries in the GeoDataFrame are valid.
    Invalid geometries are repaired with make_valid; any that end up empty
    (nothing left to keep) are removed.

    Parameters:
    gdf (GeoDataFrame): The input GeoDataFrame with geometries to be validated.

    Returns:
    GeoDataFrame: A new GeoDataFrame with all geometries valid.
    """
    fixed = gdf.copy()
    fixed['geom'] = fixed['geom'].make_valid()
    valid_gdf = fixed[fixed['geom'].notna() & ~fixed['geom'].is_empty]

    print(f"Processed {len(gdf)} geometries. {len(valid_gdf)} valid geometries remain.")
    return valid_gdf


def simplify_geometries(gdf, tolerance_meters=5, temp_crs=None):
    """
    Simplify geometries using Douglas-Peucker algorithm.

    Args:
        gdf: GeoDataFrame with geometries to simplify
        tolerance_meters: Simplification tolerance in meters
        temp_crs: CRS to use for simplification (should be in meters). Defaults
            to the data's local UTM zone, where a meter is a real meter (Web
            Mercator stretches distances away from the equator: 2x at 60 deg).

    Returns:
        GeoDataFrame with simplified geometries
    """
    if gdf.empty:
        return gdf.copy()
    original_crs = gdf.crs
    gdf_projected = gdf.to_crs(temp_crs or gdf.estimate_utm_crs())

    gdf_projected['geom'] = gdf_projected['geom'].simplify(tolerance_meters)

    result_gdf = gdf_projected.to_crs(original_crs)
    return result_gdf


def loop_remove_small_holes(geom, min_hole_area_sqm=2000):
        if geom is None or geom.geom_type not in ['Polygon', 'MultiPolygon']:
            return geom

        if geom.geom_type == 'Polygon':
            exterior = geom.exterior
            holes = [hole for hole in geom.interiors 
                    if abs(Polygon(hole).area) >= min_hole_area_sqm]
            return Polygon(exterior, holes)

        elif geom.geom_type == 'MultiPolygon':
            new_polygons = []
            for poly in geom.geoms:
                exterior = poly.exterior
                holes = [hole for hole in poly.interiors 
                        if abs(Polygon(hole).area) >= min_hole_area_sqm]
                new_polygons.append(Polygon(exterior, holes))
            return MultiPolygon(new_polygons)

        return geom


def remove_small_holes(gdf, min_hole_area_sqm=2000, temp_crs="EPSG:6933"):
    """
    Remove holes smaller than specified area from polygons.
    
    Args:
        gdf: GeoDataFrame with polygons
        min_hole_area_sqm: Minimum hole area in square meters
        temp_crs: CRS to use for area calculations. Defaults to an equal-area
            CRS (EPSG:6933), so areas are true square meters at any latitude
            (Web Mercator inflates them: 2x at 45 deg, 4x at 60 deg).
        
    Returns:
        GeoDataFrame with small holes removed
    """
    if gdf.empty:
        return gdf.copy()

    original_crs = gdf.crs
    gdf_projected = gdf.to_crs(temp_crs)

    gdf_projected['geom'] = gdf_projected['geom'].apply(loop_remove_small_holes, min_hole_area_sqm=min_hole_area_sqm)

    result_gdf = gdf_projected.to_crs(original_crs)
    return result_gdf


def drop_duplicate_geometries(gdf):
    """
    Drop duplicate geometries from a GeoDataFrame, keeping one instance of each geometry.

    Parameters:
    gdf (GeoDataFrame): Input GeoDataFrame
    tolerance (float): Tolerance for considering geometries as duplicates

    Returns:
    GeoDataFrame: GeoDataFrame with duplicate geometries removed
    """
    gdf['geometry_wkb'] = gdf.geometry.apply(lambda geom: geom.wkb)
    gdf_unique = gdf.drop_duplicates(subset='geometry_wkb')
    gdf_unique = gdf_unique.drop(columns=['geometry_wkb'])

    return gdf_unique


def export_layer(gdf, output_layer_name: str,
                 file_type: str = 'geojson',
                 layers_dir: str = None):
    """
    Export a GeoDataFrame to GeoJSON or PMTiles format.

    Args:
        gdf: GeoDataFrame to export
        output_layer_name: Name for the output file (without extension)
        file_type: 'geojson' or 'pmtiles' (default: 'geojson')
        layers_dir: Path to layers directory (default: '../app/layers')

    Raises:
        ValueError: If file_type is not 'geojson' or 'pmtiles'
    """
    if file_type not in ('geojson', 'pmtiles'):
        raise ValueError(f"file_type must be 'geojson' or 'pmtiles', got '{file_type}'")

    if layers_dir is None:
        layers_dir = os.path.join('..', 'app', 'layers')

    os.makedirs(layers_dir, exist_ok=True)

    if file_type == 'geojson':
        output_file_path = os.path.join(layers_dir, f'{output_layer_name}.geojson')
        gdf.to_file(output_file_path, driver='GeoJSON')
        print(f"Exported to GeoJSON: {output_file_path}")

    elif file_type == 'pmtiles':
        output_file_path = os.path.join(layers_dir, f'{output_layer_name}.pmtiles')
        to_write = gdf if gdf.crs is not None and gdf.crs.to_epsg() == 4326 else gdf.to_crs(4326)
        to_write.to_file(output_file_path, driver='PMTiles')
        print(f"Exported to PMTiles: {output_file_path}")


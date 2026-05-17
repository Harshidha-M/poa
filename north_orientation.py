import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import matplotlib.pyplot as plt

print("STARTING...")

# =====================================================
# INPUT FILE
# =====================================================

input_file = r"F:\POA\Delhi_Building_Orientation.gpkg"

# =====================================================
# OUTPUT TIFF
# =====================================================

output_tif = r"F:\POA\Delhi_Building_Orientation_North.tif"

# =====================================================
# LOAD ONLY REQUIRED COLUMNS
# =====================================================

print("LOADING DATA...")

gdf = gpd.read_file(
    input_file,
    columns=["North Aligned", "geometry"]
)

# =====================================================
# REMOVE NULLS
# =====================================================

print("REMOVING NULLS...")

gdf = gdf[
    gdf.geometry.notnull()
]

gdf = gdf[
    gdf["North Aligned"].notnull()
]

# =====================================================
# PROJECT TO METRIC CRS
# =====================================================

print("PROJECTING CRS...")

gdf = gdf.to_crs("EPSG:32643")

# =====================================================
# REMOVE VERY SMALL BUILDINGS
# =====================================================

print("REMOVING SMALL BUILDINGS...")

gdf = gdf[
    gdf.geometry.area > 20
]

# =====================================================
# FEATURE COUNT
# =====================================================

print("\nTOTAL BUILDINGS:", len(gdf))

# =====================================================
# RASTER RESOLUTION
# =====================================================

pixel_size = 20

# =====================================================
# GET BOUNDS
# =====================================================

minx, miny, maxx, maxy = gdf.total_bounds

print("\nBOUNDS:")
print(minx, miny, maxx, maxy)

# =====================================================
# RASTER SIZE
# =====================================================

width = int((maxx - minx) / pixel_size)
height = int((maxy - miny) / pixel_size)

print("\nRASTER SIZE:")
print(width, height)

# =====================================================
# TRANSFORM
# =====================================================

transform = from_bounds(
    minx,
    miny,
    maxx,
    maxy,
    width,
    height
)

# =====================================================
# SHAPES
# =====================================================

print("\nPREPARING SHAPES...")

shapes = (
    (geom, value)
    for geom, value in zip(
        gdf.geometry,
        gdf["North Aligned"]
    )
)

# =====================================================
# RASTERIZE
# =====================================================

print("\nRASTERIZING...")

orientation_raster = rasterize(
    shapes=shapes,
    out_shape=(height, width),
    transform=transform,
    fill=np.nan,
    dtype="float32"
)

# =====================================================
# SAVE TIFF
# =====================================================

print("\nSAVING TIFF...")

with rasterio.open(
    output_tif,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype="float32",
    crs=gdf.crs,
    transform=transform,
    nodata=np.nan,
    compress="lzw"
) as dst:

    dst.write(
        orientation_raster,
        1
    )

print("\nTIFF SAVED:")
print(output_tif)

# =====================================================
# FULL 360° BUILDING ORIENTATIONS
# =====================================================

print("\nPREPARING FULL 360° ORIENTATIONS...")

# Original orientations
angles = gdf["North Aligned"].values

# Convert to 0–180
angles = angles % 180

# Duplicate to full 360°
angles_full = np.concatenate([
    angles,
    angles + 180
])

# =====================================================
# SHIFTED 10° BINS
# =====================================================

bins = np.arange(-5, 366, 10)

# =====================================================
# FULL 360° HISTOGRAM
# =====================================================

print("\nCREATING HISTOGRAM...")

plt.figure(figsize=(14,6))

plt.hist(
    angles_full,
    bins=bins,
    edgecolor="black",
    rwidth=0.9
)

# Clean x labels
plt.xticks(
    np.arange(0, 361, 30)
)

plt.xlabel("Building Orientation (Degrees)")
plt.ylabel("Building Count")

plt.title(
    "Full 360° Building Orientation Histogram"
)

plt.grid(True)

plt.show()

# =====================================================
# FULL 360° ROSE DIAGRAM
# =====================================================

print("\nCREATING FULL ROSE DIAGRAM...")

# Histogram for rose diagram
counts, bin_edges = np.histogram(
    angles_full,
    bins=bins
)

# =====================================================
# FORCE SYMMETRY (VISUAL ONLY)
# =====================================================

half = len(counts) // 2

for i in range(half):

    avg = (
        counts[i] +
        counts[i + half]
    ) / 2

    counts[i] = avg
    counts[i + half] = avg

# =====================================================
# BIN CENTERS
# =====================================================

bin_centers = (
    bin_edges[:-1] +
    bin_edges[1:]
) / 2

# =====================================================
# CONVERT TO RADIANS
# =====================================================

theta = np.deg2rad(
    bin_centers
)

# =====================================================
# SECTOR WIDTH
# =====================================================

width = np.deg2rad(10)

# =====================================================
# POLAR FIGURE
# =====================================================

fig = plt.figure(figsize=(10,10))

ax = fig.add_subplot(
    111,
    projection="polar"
)

# =====================================================
# POLAR BARS
# =====================================================

bars = ax.bar(
    theta,
    counts,
    width=width,
    bottom=0,
    
)

# =====================================================
# NORTH ON TOP
# =====================================================

ax.set_theta_zero_location("N")

# =====================================================
# CLOCKWISE ROTATION
# =====================================================

ax.set_theta_direction(-1)

# =====================================================
# CLEAN DEGREE LABELS
# =====================================================

ax.set_thetagrids(
    np.arange(0, 360, 30)
)

# =====================================================
# TITLE
# =====================================================

ax.set_title(
    "Full 360° Building Orientation Rose Diagram",
    pad=30,
    fontsize=14
)

plt.show()

print("\nDONE.")

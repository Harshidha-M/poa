import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import matplotlib.pyplot as plt


input_file = r"F:\POA\Delhi_Building_Orientation.gpkg"

output_tif = r"F:\POA\Delhi_Building_Orientation_North.tif"

# =====================================================
# LOAD ONLY REQUIRED COLUMNS
# =====================================================

gdf = gpd.read_file(
    input_file,
    columns=["North Aligned", "geometry"]
)

# =====================================================
# REMOVE NULLS
# =====================================================

gdf = gdf[
    gdf.geometry.notnull()
]

gdf = gdf[
    gdf["North Aligned"].notnull()
]

# =====================================================
# PROJECT TO METRIC CRS FIRST
# =====================================================

gdf = gdf.to_crs("EPSG:32643")

# =====================================================
# REMOVE VERY SMALL BUILDINGS
# =====================================================

gdf = gdf[
    gdf.geometry.area > 20
]

# =====================================================
# CHECK FEATURE COUNT
# =====================================================

print("TOTAL BUILDINGS :", len(gdf))

# =====================================================
# RASTER RESOLUTION
# =====================================================

pixel_size = 20

# =====================================================
# GET BOUNDS
# =====================================================

minx, miny, maxx, maxy = gdf.total_bounds

print(minx, miny, maxx, maxy)

# =====================================================
# RASTER SIZE
# =====================================================

width = int((maxx - minx) / pixel_size)
height = int((maxy - miny) / pixel_size)

print("Raster size:", width, height)

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
# ADD HERE
# =====================================================

# YOUR HISTOGRAM + CIRCULAR PLOT CODE

# =====================================================
# DISPLAY
# =====================================================

plt.figure(figsize=(10,10))

# =====================================================
# ORIENTATION VALUES
# =====================================================

angles = gdf["North Aligned"].values

# =====================================================
# CONVERT TO 0–180
# =====================================================

angles_180 = angles % 180

# =====================================================
# 10 DEGREE BINS
# =====================================================

bins = np.arange(0, 181, 10)

# =====================================================
# HISTOGRAM
# =====================================================

plt.figure(figsize=(12,6))

plt.hist(
    angles_180,
    bins=bins,
    edgecolor="black"
)

plt.xticks(bins)

plt.xlabel("Orientation (Degrees)")
plt.ylabel("Building Count")

plt.title("180° Building Orientation Histogram")

plt.grid(True)

plt.show()


# =====================================================
# FULL 360° ROSE DIAGRAM
# =====================================================

print("CREATING FULL ROSE DIAGRAM...")

# Original angles
angles = gdf["North Aligned"].values

# Convert to 0–180
angles = angles % 180

# Duplicate to make full circular symmetry
angles_full = np.concatenate([
    angles,
    angles + 180
])

# Bins every 10 degrees
bins = np.arange(0, 361, 10)

# Histogram
counts, bin_edges = np.histogram(
    angles_full,
    bins=bins
)

# Bin centers
bin_centers = (
    bin_edges[:-1] + bin_edges[1:]
) / 2

# Convert to radians
theta = np.deg2rad(bin_centers)

# Sector width
width = np.deg2rad(10)

# =====================================================
# POLAR PLOT
# =====================================================

fig = plt.figure(figsize=(10,10))

ax = fig.add_subplot(
    111,
    projection="polar"
)

bars = ax.bar(
    theta,
    counts,
    width=width,
    bottom=0
)

# North on top
ax.set_theta_zero_location("N")

# Clockwise
ax.set_theta_direction(-1)

# Degree labels
ax.set_thetagrids(
    np.arange(0, 360, 30)
)

ax.set_title(
    "Full 360° Building Orientation Rose Diagram",
    pad=30,
    fontsize=14
)

plt.show()

# -*- coding: utf-8 -*-
"""
FULL BUILDING ORIENTATION ANALYSIS

OUTPUTS:
1. Orientation Raster
2. Full 360° Histogram
3. Full 360° Rose Diagram
4. Shannon Entropy
5. Orientation Order (phi)

@author: harshi
"""

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import matplotlib.pyplot as plt
from scipy.stats import entropy

print("STARTING...")

# =====================================================
# INPUT FILE
# =====================================================

input_file = r"F:\POA\Delhi_Building_Footprints.gpkg"

# =====================================================
# OUTPUT TIFF
# =====================================================

output_tif = r"F:\POA\Building_Orientation_North.tif"

# =====================================================
# LOAD DATA
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
# DISPLAY ORIENTATION RASTER
# =====================================================

print("\nDISPLAYING ORIENTATION RASTER...")

plt.figure(figsize=(10,10))

plt.imshow(
    orientation_raster,
    cmap="hsv"
)

plt.colorbar(
    label="Orientation wrt North"
)

plt.title(
    "Building Orientation Raster"
)

plt.axis("off")

plt.show()

# =====================================================
# BUILDING ORIENTATIONS
# =====================================================

print("\nPREPARING ORIENTATIONS...")

angles = gdf["North Aligned"].values

# =====================================================
# CONVERT TO 0–180
# =====================================================

angles = angles % 180

# =====================================================
# DUPLICATE TO FULL 360°
# =====================================================

angles_full = np.concatenate([
    angles,
    angles + 180
])

# =====================================================
# SHIFTED 10° BINS
# =====================================================

bins = np.arange(-5, 366, 10)

# =====================================================
# HISTOGRAM COUNTS
# =====================================================

counts, edges = np.histogram(
    angles_full,
    bins=bins
)

# =====================================================
# REMOVE EMPTY BINS
# =====================================================

counts_nonzero = counts[
    counts > 0
]

# =====================================================
# PROBABILITIES
# =====================================================

probabilities = (
    counts_nonzero /
    counts_nonzero.sum()
)

# =====================================================
# SHANNON ENTROPY
# =====================================================

H = entropy(
    probabilities,
    base=np.e
)

print("\n===================================")
print("SHANNON ENTROPY")
print("===================================")

print(H)

# =====================================================
# MAXIMUM ENTROPY
# =====================================================

n_bins = 36

Hmax = np.log(n_bins)

print("\n===================================")
print("MAXIMUM ENTROPY")
print("===================================")

print(Hmax)

# =====================================================
# NORMALIZED ORIENTATION ORDER
# =====================================================

phi = 1 - (H / Hmax)

print("\n===================================")
print("NORMALIZED ORIENTATION ORDER")
print("===================================")

print(phi)

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

# clean labels
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

print("\nCREATING ROSE DIAGRAM...")

# histogram again for rose
counts_rose, edges_rose = np.histogram(
    angles_full,
    bins=bins
)

# =====================================================
# OPTIONAL SYMMETRY FIX
# =====================================================

half = len(counts_rose) // 2

for i in range(half):

    avg = (
        counts_rose[i] +
        counts_rose[i + half]
    ) / 2

    counts_rose[i] = avg
    counts_rose[i + half] = avg

# =====================================================
# BIN CENTERS
# =====================================================

centers = (
    edges_rose[:-1] +
    edges_rose[1:]
) / 2

# =====================================================
# CONVERT TO RADIANS
# =====================================================

theta = np.deg2rad(
    centers
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

ax.bar(
    theta,
    counts_rose,
    width=width,
    bottom=0
)

# =====================================================
# NORTH ON TOP
# =====================================================

ax.set_theta_zero_location("N")

# =====================================================
# CLOCKWISE
# =====================================================

ax.set_theta_direction(-1)

# =====================================================
# DEGREE LABELS
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

# =====================================================
# FINAL INTERPRETATION
# =====================================================

print("\n===================================")
print("INTERPRETATION")
print("===================================")

if phi > 0.75:

    print(
        "Highly ordered building orientation pattern."
    )

elif phi > 0.5:

    print(
        "Moderately ordered building orientation pattern."
    )

else:

    print(
        "Highly disordered/random building orientation pattern."
    )

print("\nDONE.")

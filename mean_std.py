import geopandas as gpd
import numpy as np
from shapely.geometry import box
import matplotlib.pyplot as plt

print("LOADING BUILDINGS...")

# =====================================================
# INPUT
# =====================================================

input_file = r"F:\POA\Chandigarh_Building_Orientation.gpkg"

mean_png = r"F:\POA\Final_Output\Chandigarh\Chandigarh_Mean_POA.png"

std_png = r"F:\POA\Final_Output\Chandigarh\Chandigarh_STD_POA.png"

# =====================================================
# OUTPUT TIFFS
# =====================================================

mean_tif = r"F:\POA\Final_Output\Chandigarh\Chandigarh_Mean_POA.tif"

std_tif = r"F:\POA\Final_Output\Chandigarh\Chandigarh_STD_POA.tif"
# =====================================================
# LOAD BUILDINGS
# =====================================================

gdf = gpd.read_file(
    input_file,
    columns=["North Aligned", "geometry"]
)

# =====================================================
# CLEAN DATA
# =====================================================

gdf = gdf[
    gdf.geometry.notnull()
]

gdf = gdf[
    gdf["North Aligned"].notnull()
]

# =====================================================
# PROJECT CRS
# =====================================================

gdf = gdf.to_crs("EPSG:32643")

# =====================================================
# REMOVE SMALL BUILDINGS
# =====================================================

gdf = gdf[
    gdf.geometry.area > 20
]

print("TOTAL BUILDINGS:", len(gdf))

# =====================================================
# CREATE GRID
# =====================================================

print("\nCREATING GRID...")

grid_size = 100

minx, miny, maxx, maxy = gdf.total_bounds

grid_cells = []

x = minx

while x < maxx:

    y = miny

    while y < maxy:

        grid_cells.append(
            box(
                x,
                y,
                x + grid_size,
                y + grid_size
            )
        )

        y += grid_size

    x += grid_size

grid = gpd.GeoDataFrame(
    geometry=grid_cells,
    crs=gdf.crs
)

print("TOTAL GRID CELLS:", len(grid))

# =====================================================
# SPATIAL JOIN
# =====================================================

print("\nSPATIAL JOIN...")

joined = gpd.sjoin(
    gdf,
    grid,
    predicate="intersects"
)

# =====================================================
# STORE RESULTS
# =====================================================

mean_list = []
std_list = []

print("\nCOMPUTING GRID STATISTICS...")

# =====================================================
# LOOP THROUGH GRID
# =====================================================

for idx in range(len(grid)):

    subset = joined[
        joined["index_right"] == idx
    ]

    # building orientations
    angles = subset["North Aligned"].values

    # remove invalid
    angles = angles[
        np.isfinite(angles)
    ]

    # convert to 0-180
    angles = angles % 180

    # skip empty
    if len(angles) == 0:

        mean_list.append(np.nan)
        std_list.append(np.nan)

        continue

    # =====================================================
    # CIRCULAR MEAN
    # IMPORTANT FOR ANGLES
    # =====================================================

    angles_rad = np.deg2rad(angles * 2)

    mean_sin = np.mean(np.sin(angles_rad))
    mean_cos = np.mean(np.cos(angles_rad))

    mean_angle = 0.5 * np.arctan2(
        mean_sin,
        mean_cos
    )

    mean_angle_deg = np.rad2deg(mean_angle)

    if mean_angle_deg < 0:
        mean_angle_deg += 180

    # =====================================================
    # ANGULAR STD
    # =====================================================

    R = np.sqrt(
        mean_sin**2 +
        mean_cos**2
    )

    # numerical stability
    R = np.clip(R, 1e-8, 0.999999)

    std_angle = np.rad2deg(
        np.sqrt(-2 * np.log(R))
    ) / 2
    
    mean_list.append(mean_angle_deg)
    std_list.append(std_angle)

# =====================================================
# ADD RESULTS
# =====================================================

grid["Mean_Orientation"] = mean_list
grid["Std_Orientation"] = std_list

# =====================================================
# REMOVE EMPTY CELLS
# =====================================================

grid = grid[
    grid["Mean_Orientation"].notnull()
]

print("\nVALID GRID CELLS:", len(grid))

# =====================================================
# PERCENTILE STRETCH
# =====================================================

mean_vmin = np.nanpercentile(
    grid["Mean_Orientation"],
    2
)

mean_vmax = np.nanpercentile(
    grid["Mean_Orientation"],
    98
)

std_vmin = np.nanpercentile(
    grid["Std_Orientation"],
    2
)

std_vmax = np.nanpercentile(
    grid["Std_Orientation"],
    98
)

# =====================================================
# MEAN ORIENTATION MAP
# =====================================================

print("\nDISPLAYING MEAN ORIENTATION...")

fig, ax = plt.subplots(
    figsize=(12,12)
)

ax.set_facecolor("white")

grid.plot(
    column="Mean_Orientation",

    cmap="plasma",

    linewidth=0,

    edgecolor="none",

    legend=True,

    ax=ax,

    vmin=mean_vmin,
    vmax=mean_vmax,

    missing_kwds={
        "color": "white"
    }
)

ax.set_title(
    "Mean Building Orientation",
    fontsize=18
)

ax.axis("off")

plt.show()

# =====================================================
# STD ORIENTATION MAP
# =====================================================

print("\nDISPLAYING STD ORIENTATION...")

fig, ax = plt.subplots(
    figsize=(12,12)
)

ax.set_facecolor("white")

grid.plot(
    column="Std_Orientation",

    cmap="plasma",

    linewidth=0,

    edgecolor="none",

    legend=True,

    ax=ax,

    vmin=std_vmin,
    vmax=std_vmax,

    missing_kwds={
        "color": "white"
    }
)

ax.set_title(
    "Orientation Standard Deviation",
    fontsize=18
)

ax.axis("off")

plt.show()

# =====================================================
# HISTOGRAM
# =====================================================

print("\nDISPLAYING HISTOGRAM...")

plt.figure(figsize=(10,6))

plt.hist(
    grid["Std_Orientation"],
    bins=40,
    edgecolor="black"
)

plt.xlabel(
    "Orientation Standard Deviation"
)

plt.ylabel(
    "Grid Count"
)

plt.title(
    "Distribution of Orientation Std Dev"
)

plt.grid(True)

plt.show()

# =====================================================
# BASIC STATS
# =====================================================

print("\n=================================")
print("MEAN ORIENTATION STATS")
print("=================================")

print("MIN :", np.nanmin(grid["Mean_Orientation"]))
print("MAX :", np.nanmax(grid["Mean_Orientation"]))
print("MEAN:", np.nanmean(grid["Mean_Orientation"]))

print("\n=================================")
print("STD ORIENTATION STATS")
print("=================================")

print("MIN :", np.nanmin(grid["Std_Orientation"]))
print("MAX :", np.nanmax(grid["Std_Orientation"]))
print("MEAN:", np.nanmean(grid["Std_Orientation"]))

print("\nDONE ✔")

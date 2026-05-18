import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import box
import matplotlib.pyplot as plt
import matplotlib.colors as colors

print("LOADING BUILDINGS...")

# =====================================================
# INPUTS
# =====================================================

building_file = r"F:\POA\Chandigarh_Building_Orientation.gpkg"

poa_raster = r"F:\POA\NISAR_L2_PR_GSLC_008_106_D_074_2005_QPDH_A_20251223T133149_20251223T133207_X05010_N_P_J_001\rlee_3x3\Chnd_T3\POA_chnd.tif"

# OUTPUT PNGS
mean_png = r"F:\POA\Final_Output\Chandigarh\Chandigarh_Mean_POA.png"

std_png = r"F:\POA\Final_Output\Chandigarh\Chandigarh_STD_POA.png"

# =====================================================
# LOAD BUILDINGS
# =====================================================

gdf = gpd.read_file(
    building_file,
    columns=["geometry"]
)

gdf = gdf[
    gdf.geometry.notnull()
]

gdf = gdf.to_crs("EPSG:32643")

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
# OPEN POA RASTER
# =====================================================

print("\nOPENING POA RASTER...")

src = rasterio.open(poa_raster)

# =====================================================
# STORE RESULTS
# =====================================================

mean_poa_list = []
std_poa_list = []

# =====================================================
# LOOP THROUGH GRID
# =====================================================

print("\nCOMPUTING STATISTICS...")

for idx, row in grid.iterrows():

    geom = [row.geometry]

    try:

        out_image, out_transform = mask(
            src,
            geom,
            crop=True
        )

        values = out_image[0]

        # remove invalid values
        values = values[
            np.isfinite(values)
        ]

        nodata = src.nodata

        if nodata is not None:

            values = values[
                values != nodata
            ]

        # remove zeros
        values = values[
            values != 0
        ]

        # valid POA range
        values = np.clip(
            values,
            -45,
            45
        )

        # skip empty
        if len(values) == 0:

            mean_poa_list.append(np.nan)
            std_poa_list.append(np.nan)

            continue

        # =====================================================
        # COMPUTE MEAN + STD
        # =====================================================

        mean_poa = np.nanmean(values)

        std_poa = np.nanstd(values)

        mean_poa_list.append(mean_poa)

        std_poa_list.append(std_poa)

    except:

        mean_poa_list.append(np.nan)
        std_poa_list.append(np.nan)

# =====================================================
# ADD RESULTS
# =====================================================

grid["Mean_POA"] = mean_poa_list

grid["Std_POA"] = std_poa_list

# =====================================================
# REMOVE EMPTY CELLS
# =====================================================

grid = grid[
    grid["Mean_POA"].notnull()
]

print("\nVALID GRID CELLS:", len(grid))

# =====================================================
# REMOVE BLACK BACKGROUND
# =====================================================

mean_data = grid["Mean_POA"].copy()
std_data = grid["Std_POA"].copy()

# =====================================================
# PERCENTILE STRETCH
# (VERY IMPORTANT FOR VISIBILITY)
# =====================================================

mean_vmin = np.nanpercentile(mean_data, 2)
mean_vmax = np.nanpercentile(mean_data, 98)

std_vmin = np.nanpercentile(std_data, 2)
std_vmax = np.nanpercentile(std_data, 98)

# =====================================================
# MEAN POA MAP
# =====================================================

print("\nCREATING MEAN POA MAP...")

fig, ax = plt.subplots(
    figsize=(12,12)
)

ax.set_facecolor("white")

grid.plot(
    column="Mean_POA",
    
    # MUCH BETTER FOR MEAN
    cmap="coolwarm",

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
    "Mean POA",
    fontsize=18
)

ax.axis("off")

plt.savefig(
    mean_png,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.show()

print("MEAN MAP SAVED:")
print(mean_png)

# =====================================================
# STD POA MAP
# =====================================================

print("\nCREATING STD POA MAP...")

fig, ax = plt.subplots(
    figsize=(12,12)
)

ax.set_facecolor("white")

grid.plot(
    column="Std_POA",

    # BETTER VISIBILITY
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
    "POA Standard Deviation",
    fontsize=18
)

ax.axis("off")

plt.savefig(
    std_png,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.show()

print("STD MAP SAVED:")
print(std_png)

# =====================================================
# HISTOGRAM
# =====================================================

plt.figure(figsize=(10,6))

plt.hist(
    grid["Std_POA"],
    bins=40,
    edgecolor="black"
)

plt.xlabel("POA Standard Deviation")
plt.ylabel("Grid Count")

plt.title(
    "Distribution of POA Standard Deviation"
)

plt.grid(True)

plt.show()

# =====================================================
# BASIC STATS
# =====================================================

print("\n=================================")
print("MEAN POA STATS")
print("=================================")

print("MIN :", np.nanmin(grid["Mean_POA"]))
print("MAX :", np.nanmax(grid["Mean_POA"]))
print("MEAN:", np.nanmean(grid["Mean_POA"]))

print("\n=================================")
print("STD POA STATS")
print("=================================")

print("MIN :", np.nanmin(grid["Std_POA"]))
print("MAX :", np.nanmax(grid["Std_POA"]))
print("MEAN:", np.nanmean(grid["Std_POA"]))

print("\nDONE ✔")

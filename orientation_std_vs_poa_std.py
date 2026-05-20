import rasterio
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, pearsonr
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import box

print("LOADING BUILDINGS...")

# =====================================================
# INPUTS
# =====================================================

building_file = r"F:\POA\Delhi_Building_Orientation.gpkg"

poa_raster = r"F:\POA\NISAR_L2_PR_GSLC_008_106_D_074_2005_QPDH_A_20251223T133149_20251223T133207_X05010_N_P_J_001\rlee_3x3\Delhi_T3\POA_delhi.tif"

# =====================================================
# LOAD BUILDINGS
# =====================================================

gdf = gpd.read_file(
    building_file,
    columns=["North Aligned", "geometry"]
)

gdf = gdf[
    gdf.geometry.notnull()
]

gdf = gdf[
    gdf["North Aligned"].notnull()
]

gdf = gdf.to_crs("EPSG:32643")

# remove tiny buildings
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
# OPEN POA RASTER
# =====================================================

print("\nOPENING POA RASTER...")

src = rasterio.open(poa_raster)

# =====================================================
# STORAGE
# =====================================================

orientation_std_list = []
poa_std_list = []

# =====================================================
# LOOP THROUGH GRID
# =====================================================

print("\nCOMPUTING STATISTICS...")

for idx, row in grid.iterrows():

    cell = row.geometry

    # =====================================================
    # BUILDINGS INSIDE GRID
    # =====================================================

    buildings = gdf[
        gdf.intersects(cell)
    ]

    angles = buildings[
        "North Aligned"
    ].values

    angles = angles[
        np.isfinite(angles)
    ]

    angles = angles % 180

    # =====================================================
    # SKIP EMPTY
    # =====================================================

    if len(angles) < 3:

        continue

    # =====================================================
    # CIRCULAR STD OF ORIENTATION
    # =====================================================

    angles_rad = np.deg2rad(
        angles * 2
    )

    mean_sin = np.mean(
        np.sin(angles_rad)
    )

    mean_cos = np.mean(
        np.cos(angles_rad)
    )

    R = np.sqrt(
        mean_sin**2 +
        mean_cos**2
    )

    # numerical stability
    R = np.clip(
        R,
        1e-8,
        0.999999
    )

    orientation_std = (
        np.rad2deg(
            np.sqrt(-2 * np.log(R))
        ) / 2
    )

    # =====================================================
    # MASK POA ONLY ON BUILDINGS
    # =====================================================

    building_geom = [
        geom
        for geom in buildings.geometry
    ]

    try:

        out_image, out_transform = mask(
            src,
            building_geom,
            crop=True
        )

        values = out_image[0]

        # remove invalid
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

        # skip sparse cells
        if len(values) < 5:

            continue

        # =====================================================
        # POA STD
        # =====================================================

        poa_std = np.nanstd(values)

        orientation_std_list.append(
            orientation_std
        )

        poa_std_list.append(
            poa_std
        )

    except:

        continue

# =====================================================
# FINAL ARRAYS
# =====================================================

ori_vals = np.array(
    orientation_std_list
)

poa_vals = np.array(
    poa_std_list
)

print("\nVALID POINTS:", len(ori_vals))

# =====================================================
# REMOVE BAD VALUES
# =====================================================

mask_valid = (
    np.isfinite(ori_vals)
    &
    np.isfinite(poa_vals)
)

ori_vals = ori_vals[
    mask_valid
]

poa_vals = poa_vals[
    mask_valid
]

# =====================================================
# OPTIONAL SUBSAMPLING
# =====================================================

max_n = 50000

if len(ori_vals) > max_n:

    idx = np.random.choice(
        len(ori_vals),
        max_n,
        replace=False
    )

    ori_vals = ori_vals[idx]
    poa_vals = poa_vals[idx]

print("FINAL POINTS:", len(ori_vals))

# =====================================================
# KDE DENSITY
# =====================================================

xy = np.vstack([
    ori_vals,
    poa_vals
])

density = gaussian_kde(
    xy
)(xy)

# sort by density
idx = density.argsort()

x = ori_vals[idx]
y = poa_vals[idx]
z = density[idx]

# =====================================================
# SCATTER PLOT
# =====================================================

print("\nCREATING DENSITY SCATTER...")

plt.figure(figsize=(12,10))

plt.scatter(
    x,
    y,
    c=z,
    s=10,
    cmap="plasma"
)

plt.colorbar(
    label="Density"
)

plt.xlabel(
    "Orientation STD"
)

plt.ylabel(
    "POA STD"
)

plt.title(
    "Orientation Disorder vs POA Disorder"
)

plt.grid(True)

plt.show()

# =====================================================
# CORRELATION
# =====================================================

corr, pval = pearsonr(
    ori_vals,
    poa_vals
)

print("\n=================================")
print("RESULTS")
print("=================================")

print("Pearson r:", corr)
print("P-value:", pval)

print("\nDONE ✔")

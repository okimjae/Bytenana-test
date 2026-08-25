import subprocess
import duckdb
import folium
import geopandas as gpd
from shapely import wkt
from src.observability.logger import logger


def generate_and_open_map():
    conn = duckdb.connect("spatial_data.duckdb")
    parcels = conn.execute(
        "SELECT parcel_id, subdivision, zone_code, is_residential, calculated_area_acres, geom_wkt FROM fct_parcels_enriched"
    ).fetchall()

    if not parcels:
        print("⚠️ No parcels found in database. Run 'python run_pipeline.py' first!")
        return

    # Center map on Buda, TX
    m = folium.Map(location=[30.083, -97.843], zoom_start=14, tiles="OpenStreetMap")

    for pid, subdiv, zone, is_res, acres, geom_str in parcels:
        poly_2277 = wkt.loads(geom_str)
        gdf = gpd.GeoDataFrame([{"geometry": poly_2277}], crs="EPSG:2277").to_crs("EPSG:4326")
        poly_4326 = gdf.geometry.iloc[0]

        color = "#27ae60" if is_res else "#2980b9"
        res_label = "✅ YES (Residential)" if is_res else "❌ NO (Commercial/Other)"
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 190px;">
            <h4 style="margin: 0 0 6px 0; color: #2c3e50; border-bottom: 2px solid {color}; padding-bottom: 4px;">Parcel {pid}</h4>
            <b>Subdivision:</b> {subdiv}<br>
            <b>Zoning:</b> {zone}<br>
            <b>Calculated Area:</b> {acres:.2f} acres<br>
            <b>Residential:</b> {res_label}
        </div>
        """

        if poly_4326.geom_type == "Polygon":
            coords = [[p[1], p[0]] for p in poly_4326.exterior.coords]
            folium.Polygon(
                locations=coords,
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=popup_html,
                tooltip=f"{pid} ({acres:.2f} ac)",
            ).add_to(m)

    # 1km radius circle (Stretch query)
    folium.Circle(
        location=[30.083, -97.843],
        radius=1000,
        color="#e74c3c",
        weight=2,
        fill=True,
        fill_opacity=0.1,
        popup="<b>1 km Proximity Radius</b><br>Downtown Buda (Optional Stretch Query)",
    ).add_to(m)

    m.save("map_preview.html")
    print("✅ map_preview.html generated successfully! Opening in browser...")
    try:
        subprocess.run(["open", "map_preview.html"])
    except Exception:
        pass


if __name__ == "__main__":
    generate_and_open_map()

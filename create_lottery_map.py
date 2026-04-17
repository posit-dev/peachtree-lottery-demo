# Georgia Lottery Sales Choropleth Map Function
# This function creates an interactive map showing how much
# on average each wage earning adult in a county spends on
# lottery tickets annually

import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
import pygris


def create_lottery_map(data, per_capita=False, state_fips="13", palette="YlOrRd"):
    """
    Create an interactive choropleth map of lottery sales by county.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame with columns: county, year, lottery_spend, and (if per_capita) n.
    per_capita : bool
        If True, show per-capita spending (total lottery_spend / total n per county-year).
        Default False.
    state_fips : str
        State FIPS code. Default "13" (Georgia).
    palette : str
        ColorBrewer palette name (e.g. "YlOrRd", "Blues"). Default "YlOrRd".

    Returns
    -------
    folium.Map
    """
    # Aggregate by county and year
    if per_capita:
        county_year_totals = (
            data.groupby(["county", "year"])
            .apply(
                lambda x: pd.Series(
                    {"dollars": x["lottery_spend"].sum(skipna=True) / x["n"].sum(skipna=True)}
                ),
                include_groups=False,
            )
            .reset_index()
        )
    else:
        county_year_totals = (
            data.groupby(["county", "year"])
            .agg(dollars=("lottery_spend", "sum"))
            .reset_index()
        )

    # Fetch county boundaries from Census TIGER/Line (mirrors tigris::counties())
    counties_geo = pygris.counties(state=state_fips, cb=True, year=2021)
    counties_geo = counties_geo.to_crs(epsg=4326)  # Transform to WGS84
    counties_geo = counties_geo.rename(columns={"NAME": "county"})

    # Join geometry with aggregated data
    map_data = counties_geo.merge(county_year_totals, on="county", how="left")
    map_data["dollars"] = map_data["dollars"].fillna(0)

    # Add formatted tooltip label
    map_data["label"] = map_data.apply(
        lambda row: f"{row['county']}: ${row['dollars']:,.2f}", axis=1
    )

    # Build colormap from branca (mirrors leaflet::colorNumeric())
    palette_attr = f"{palette}_09"
    colormap_base = getattr(cm.linear, palette_attr, cm.linear.YlOrRd_09)
    colormap = colormap_base.scale(map_data["dollars"].min(), map_data["dollars"].max())
    colormap.caption = "Dollars"

    def style_function(feature):
        val = feature["properties"].get("dollars")
        return {
            "fillColor": colormap(val) if val is not None else "#808080",
            "color": "#FFFFFF",
            "weight": 1,
            "smoothFactor": 0.5,
            "fillOpacity": 0.7,
        }

    def highlight_function(feature):
        return {
            "weight": 2,
            "color": "#666666",
            "fillOpacity": 0.9,
        }

    m = folium.Map(location=[32.5, -83.5], zoom_start=7)

    folium.GeoJson(
        map_data,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["label"],
            aliases=[""],
            labels=False,
            sticky=True,
            style="font-weight: normal; padding: 3px 8px; font-size: 15px;",
        ),
    ).add_to(m)

    colormap.add_to(m)

    return m

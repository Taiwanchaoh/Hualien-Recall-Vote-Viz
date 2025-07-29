import dash_bootstrap_components as dbc
from utils import get_axis_title, scatter_configs
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, Input, Output, State, html

x_axis_options = ['legislator_total_voter_density', 'recall_vote_total_voter_density']

def calculate_consistent_ranges(df, upper_col, lower_col, x_axis_column):
    """
    Calculate consistent ranges for scatter plots.

    Args:
        upper_col (str): Column name for upper scatter plot
        lower_col (str): Column name for lower scatter plot
        x_axis_column (str): Column name for x-axis

    Returns:
        tuple: (x_range, y_range, color_range)
    """
    # Calculate x range with padding
    x_max = df[x_axis_column].max()
    x_range = [-x_max * 0.02, x_max * 1.02]

    # Calculate y range based on both columns
    if "rate" in upper_col.lower() and "rate" in lower_col.lower():
        # Both are rate columns, use [0, 1] range with padding
        y_range = [0, 1.05]
        color_range = [0, 1.05]
    else:
        # Calculate max value across both columns for consistent range
        max_val = max(df[upper_col].max(), df[lower_col].max())
        y_range = [0, max_val * 1.05]
        color_range = [0, max_val * 1.05]

    return x_range, y_range, color_range


def create_scatter_plot(
    df,
    y_column,
    x_column,
    highlight_index=None,
    x_range=None,
    y_range=None,
    color_range=None,
    x_title=None,
    y_title=None,
):
    """
    Create a scatter plot with optional highlighting and consistent ranges.

    Args:
        y_column (str): Column name for y-axis
        x_column (str): Column name for x-axis
        highlight_index (int, optional): Index of point to highlight
        x_range (list, optional): X-axis range [min, max]
        y_range (list, optional): Y-axis range [min, max]
        color_range (list, optional): Color bar range [min, max]
        x_title (str, optional): X-axis title
        y_title (str, optional): Y-axis title

    Returns:
        plotly.graph_objects.Figure: The scatter plot figure
    """
    # Determine color scale and ranges if not provided
    if "rate" in y_column.lower():
        if color_range is None:
            color_range = [0, 1]
        if y_range is None:
            y_range = [0, 1]
        color_scale = "RdYlGn"
    else:
        if color_range is None:
            color_range = [0, df[y_column].max()]
        if y_range is None:
            y_range = [0, df[y_column].max()]
        color_scale = "Viridis"

    # Set x_range if not provided
    if x_range is None:
        x_range = [df[x_column].min(), df[x_column].max()]

    # Create the scatter plot
    fig = px.scatter(
        df,
        x=x_column,
        y=y_column,
        hover_name="area_name",
        hover_data=[y_column, x_column, "region"],
        color=y_column,
        color_continuous_scale=color_scale,
        range_color=color_range,
    )

    # Add highlight if specified
    if highlight_index is not None and 0 <= highlight_index < len(df):
        fig.add_trace(
            go.Scatter(
                x=[df.iloc[highlight_index][x_column]],
                y=[df.iloc[highlight_index][y_column]],
                mode="markers",
                marker=dict(size=15, color="red", symbol="diamond", line=dict(width=2, color="black")),
                name="Highlighted",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Update layout with consistent ranges and titles
    layout_updates = {
        "height": 280,
        "margin": {"r": 10, "t": 40, "l": 10, "b": 10},
        "title_x": 0.5,
        "xaxis": dict(range=x_range),
        "yaxis": dict(range=y_range),
        "coloraxis": dict(colorbar=dict(title="")),  # Remove colorbar title
    }

    # Add axis titles if provided
    if x_title:
        layout_updates["xaxis"]["title"] = x_title
    if y_title:
        layout_updates["yaxis"]["title"] = y_title

    fig.update_layout(**layout_updates)

    return fig


def create_map_plot(df, selected_column, highlight_index=None, colorbar_title=None):
    """
    Create a choropleth map with optional highlighting.

    Args:
        selected_column (str): Column name to visualize on the map
        highlight_index (int, optional): Index of polygon to highlight
        colorbar_title (str, optional): Title for the colorbar

    Returns:
        plotly.graph_objects.Figure: The choropleth map figure
    """
    if not selected_column:
        return go.Figure()

    # Determine color scale range
    if "rate" in selected_column.lower():
        color_range = [0, 1]
        color_scale = "RdYlGn"
    else:
        max_val = df[selected_column].max()
        color_range = [0, max_val]
        color_scale = "Viridis"

    # Create choropleth map
    fig = px.choropleth_mapbox(
        df,
        geojson=df.geometry.__geo_interface__,
        locations=df.index,
        color=selected_column,
        hover_name="area_name",
        hover_data=[selected_column, "region"],
        color_continuous_scale=color_scale,
        range_color=color_range,
        mapbox_style="carto-positron",
        zoom=8,
        center={"lat": df.geometry.centroid.y.mean(), "lon": df.geometry.centroid.x.mean()},
        opacity=0.7,
    )

    # Add highlighted polygon if highlight_index is set
    if highlight_index is not None and 0 <= highlight_index < len(df):
        # Get the highlighted geometry
        highlighted_geom = df.iloc[highlight_index].geometry

        # Handle both single polygons and multipolygons
        if highlighted_geom.geom_type == "Polygon":
            # Single polygon
            coords = list(highlighted_geom.exterior.coords)
            lons = [coord[0] for coord in coords]
            lats = [coord[1] for coord in coords]

            fig.add_trace(
                go.Scattermapbox(
                    lon=lons,
                    lat=lats,
                    mode="lines",
                    line=dict(width=3, color="red"),
                    fill="toself",
                    fillcolor="rgba(255, 0, 0, 0.2)",
                    name="Highlighted",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
        elif highlighted_geom.geom_type == "MultiPolygon":
            # Multipolygon - add each polygon as a separate trace
            for i, polygon in enumerate(highlighted_geom.geoms):
                coords = list(polygon.exterior.coords)
                lons = [coord[0] for coord in coords]
                lats = [coord[1] for coord in coords]

                fig.add_trace(
                    go.Scattermapbox(
                        lon=lons,
                        lat=lats,
                        mode="lines",
                        line=dict(width=3, color="red"),
                        fill="toself",
                        fillcolor="rgba(255, 0, 0, 0.2)",
                        name=f"Highlighted_{i}",
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

    # Prepare colorbar configuration
    colorbar_config = dict(x=0.5, y=-0.1, xanchor="center", yanchor="top", orientation="h", len=0.8, thickness=15)

    # Add title to colorbar if provided
    if colorbar_title:
        colorbar_config["title"] = colorbar_title

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=600,
        title=f"Choropleth Map: {selected_column}",
        title_x=0.5,
        coloraxis_colorbar=colorbar_config,
    )

    return fig


def create_cross_scatter_plot(df, x_column, y_column, highlight_index=None):
    """
    Create a cross analysis scatter plot with diagonal line and trend line.
    
    Args:
        df: DataFrame containing the data
        x_column (str): Column name for x-axis
        y_column (str): Column name for y-axis
        highlight_index (int, optional): Index of point to highlight
        
    Returns:
        plotly.graph_objects.Figure: The scatter plot figure
    """
    # Calculate consistent range for both x and y axes
    x_max = df[x_column].max()
    y_max = df[y_column].max()
    
    # Use the wider range for both axes, with minimum of 0
    axis_max = max(x_max, y_max)
    
    # Add padding to the range
    axis_range = [0, axis_max * 1.05]
    
    # Create the scatter plot
    fig = px.scatter(
        df,
        x=x_column,
        y=y_column,
        hover_name="area_name",
        hover_data=[x_column, y_column, "region"],
        color=y_column,
        color_continuous_scale="Viridis",
    )
    
    # Add diagonal line (y = x)
    fig.add_trace(
        go.Scatter(
            x=[axis_range[0], axis_range[1]],
            y=[axis_range[0], axis_range[1]],
            mode="lines",
            line=dict(color="grey", width=2, dash="dash"),
            name="Diagonal (y=x)",
            showlegend=False,
        )
    )
    
    # Add highlight if specified
    if highlight_index is not None and 0 <= highlight_index < len(df):
        fig.add_trace(
            go.Scatter(
                x=[df.iloc[highlight_index][x_column]],
                y=[df.iloc[highlight_index][y_column]],
                mode="markers",
                marker=dict(size=15, color="red", symbol="diamond", line=dict(width=2, color="black")),
                name="Highlighted",
                showlegend=False,
                hoverinfo="skip",
            )
        )
    
    # Update layout with consistent axis ranges
    fig.update_layout(
        height=280,
        margin={"r": 10, "t": 40, "l": 10, "b": 10},
        title_x=0.5,
        xaxis=dict(
            title=get_axis_title(x_column),
            range=axis_range
        ),
        yaxis=dict(
            title=get_axis_title(y_column),
            range=axis_range
        ),
        coloraxis=dict(colorbar=dict(title="")),
    )
    
    return fig


def create_initial_cross_scatter_plots(df):
    """Create initial cross analysis scatter plots."""
    # Cross upper scatter: x=legislator_rate, y=against_recall_rate
    cross_upper_fig = create_cross_scatter_plot(df, "legislator_rate", "against_recall_rate")
    
    # Cross lower scatter: x=legislator_vote, y=against_recall_vote
    cross_lower_fig = create_cross_scatter_plot(df, "legislator_vote", "against_recall_vote")
    
    return cross_upper_fig, cross_lower_fig


# Create initial scatter plots
def create_initial_scatter_plots(df):
    """Create initial scatter plots with default values."""
    config = scatter_configs["Support vote rate"]
    upper_col = config["upper"]
    lower_col = config["lower"]
    x_axis = "legislator_total_voter_density"

    # Calculate consistent ranges for both plots
    x_range, y_range, color_range = calculate_consistent_ranges(df, upper_col, lower_col, x_axis)

    upper_fig = create_scatter_plot(
        df,
        upper_col,
        x_axis,
        x_range=x_range,
        y_range=y_range,
        color_range=color_range,
        x_title=get_axis_title(x_axis),
        y_title=get_axis_title(upper_col),
    )

    lower_fig = create_scatter_plot(
        df,
        lower_col,
        x_axis,
        x_range=x_range,
        y_range=y_range,
        color_range=color_range,
        x_title=get_axis_title(x_axis),
        y_title=get_axis_title(lower_col),
    )

    return upper_fig, lower_fig


def create_map_data_layout(df):
    # Create controls card
    controls = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("地圖分析", className="fw-bold"),
                                    dcc.Dropdown(
                                        id="main-dropdown",
                                        options=[
                                            {"label": get_axis_title(col), "value": col}
                                            for col in df.columns
                                            if col not in ["geometry"]
                                        ],
                                        value="legislator_rate",
                                        placeholder="Select column to visualize",
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("散布圖 y軸", className="fw-bold"),
                                    dcc.Dropdown(
                                        id="y-axis-dropdown",
                                        options=[
                                            {"label": get_axis_title(key), "value": key}
                                            for key in scatter_configs.keys()
                                        ],
                                        value="Support vote rate",
                                        placeholder="Select Y-axis type",
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("散布圖 x軸", className="fw-bold"),
                                    dcc.Dropdown(
                                        id="x-axis-dropdown",
                                        options=[
                                            {"label": get_axis_title(col), "value": col} for col in x_axis_options
                                        ],
                                        value="legislator_total_voter_density",
                                        placeholder="Select X-axis",
                                    ),
                                ],
                                width=4,
                            ),
                        ]
                    )
                ]
            )
        ],
        className="mb-3",
    )
    upper_fig, lower_fig = create_initial_scatter_plots(df)
    cross_upper_fig, cross_lower_fig = create_initial_cross_scatter_plots(df)
    return [
        # Controls
        dbc.Row([dbc.Col(controls, width=12)]),
        # Main content area with two columns
        dbc.Row(
            [
                # Left column - Map
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader([html.H3("地圖分析", className="text-center mb-0")]),
                                dbc.CardBody([dcc.Graph(id="map-graph", figure=create_map_plot(df, "legislator_rate"), style={"height": "600px"})]),
                            ]
                        )
                    ],
                    width=6,
                ),
                # Right column - Scatter plots
                dbc.Col(
                    dbc.Tabs([
                        dbc.Tab(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader([html.H3("2024 立委選舉", className="text-center mb-0")]),
                                        dbc.CardBody(
                                            [dcc.Graph(id="upper-scatter", figure=upper_fig, style={"height": "280px"})]
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader([html.H3("2025 罷免案", className="text-center mb-0")]),
                                        dbc.CardBody(
                                            [
                                                dcc.Graph(id="lower-scatter", figure=lower_fig, style={"height": "280px"}),
                                            ]
                                        ),
                                    ]
                                ),
                            ],
                            label="2024/2025 獨立分析",
                            
                        ),
                        dbc.Tab(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader([html.H3("得票率分析", className="text-center mb-0")]),
                                        dbc.CardBody(
                                            [dcc.Graph(id="cross-upper-scatter", figure=cross_upper_fig, style={"height": "280px"})]
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader([html.H3("得票數分析", className="text-center mb-0")]),
                                        dbc.CardBody(
                                            [
                                                dcc.Graph(id="cross-lower-scatter", figure=cross_lower_fig, style={"height": "280px"}),
                                            ]
                                        ),
                                    ]
                                ),
                            ],
                            label="2024/2025 跨度分析",
                        )
                    ]),
                    width=6,
                ),
            ]
        ),
    ]


def create_calloutpus(app, df):
    @app.callback(
        Output("upper-scatter", "figure", allow_duplicate=True),
        Output("lower-scatter", "figure", allow_duplicate=True),
        Output("cross-upper-scatter", "figure", allow_duplicate=True),
        Output("cross-lower-scatter", "figure", allow_duplicate=True),
        Output("map-graph", "figure", allow_duplicate=True),
        [
            Input("map-graph", "hoverData"),
            Input("upper-scatter", "hoverData"),
            Input("lower-scatter", "hoverData"),
            Input("cross-upper-scatter", "hoverData"),
            Input("cross-lower-scatter", "hoverData"),
            State("y-axis-dropdown", "value"),
            State("x-axis-dropdown", "value"),
            State("main-dropdown", "value"),
            State("map-graph", "figure"),
        ],
        prevent_initial_call=True,
    )
    def update_all_visualizations_with_highlight(
        map_hoverData, upper_hoverData, lower_hoverData, cross_upper_hoverData, cross_lower_hoverData, y_axis_type, x_axis_column, main_dropdown, current_map_fig
    ):
        if not y_axis_type or not x_axis_column or not main_dropdown:
            return go.Figure(), go.Figure(), go.Figure(), go.Figure()

        config = scatter_configs[y_axis_type]
        upper_col = config["upper"]
        lower_col = config["lower"]

        # Determine highlight index from any hover data
        highlight_index = None

        # Check map hover data
        if (
            map_hoverData
            and "points" in map_hoverData
            and len(map_hoverData["points"]) > 0
            and "pointIndex" in map_hoverData["points"][0]
        ):
            hovered_point = map_hoverData["points"][0]
            hovered_index = hovered_point["pointIndex"]
            if 0 <= hovered_index < len(df):
                highlight_index = hovered_index

        # Check upper scatter hover data
        elif (
            upper_hoverData
            and "points" in upper_hoverData
            and len(upper_hoverData["points"]) > 0
            and "pointIndex" in upper_hoverData["points"][0]
        ):
            hovered_point = upper_hoverData["points"][0]
            hovered_index = hovered_point["pointIndex"]
            if 0 <= hovered_index < len(df):
                highlight_index = hovered_index

        # Check lower scatter hover data
        elif (
            lower_hoverData
            and "points" in lower_hoverData
            and len(lower_hoverData["points"]) > 0
            and "pointIndex" in lower_hoverData["points"][0]
        ):
            hovered_point = lower_hoverData["points"][0]
            hovered_index = hovered_point["pointIndex"]
            if 0 <= hovered_index < len(df):
                highlight_index = hovered_index

        # Check cross upper scatter hover data
        elif (
            cross_upper_hoverData
            and "points" in cross_upper_hoverData
            and len(cross_upper_hoverData["points"]) > 0
            and "pointIndex" in cross_upper_hoverData["points"][0]
        ):
            hovered_point = cross_upper_hoverData["points"][0]
            hovered_index = hovered_point["pointIndex"]
            if 0 <= hovered_index < len(df):
                highlight_index = hovered_index

        # Check cross lower scatter hover data
        elif (
            cross_lower_hoverData
            and "points" in cross_lower_hoverData
            and len(cross_lower_hoverData["points"]) > 0
            and "pointIndex" in cross_lower_hoverData["points"][0]
        ):
            hovered_point = cross_lower_hoverData["points"][0]
            hovered_index = hovered_point["pointIndex"]
            if 0 <= hovered_index < len(df):
                highlight_index = hovered_index

            # Calculate consistent ranges for both plots
        x_range, y_range, color_range = calculate_consistent_ranges(df, upper_col, lower_col, x_axis_column)

        # Create scatter plots using the helper function with consistent ranges
        upper_fig = create_scatter_plot(
            df,
            upper_col,
            x_axis_column,
            highlight_index,
            x_range=x_range,
            y_range=y_range,
            color_range=color_range,
            x_title=get_axis_title(x_axis_column),
            y_title=get_axis_title(upper_col),
        )

        lower_fig = create_scatter_plot(
            df,
            lower_col,
            x_axis_column,
            highlight_index,
            x_range=x_range,
            y_range=y_range,
            color_range=color_range,
            x_title=get_axis_title(x_axis_column),
            y_title=get_axis_title(lower_col),
        )
        
        cross_upper_fig = create_cross_scatter_plot(df, "legislator_rate", "against_recall_rate", highlight_index)
        cross_lower_fig = create_cross_scatter_plot(df, "legislator_vote", "against_recall_vote", highlight_index)

        # Handle map highlighting by adding traces to existing map
        if current_map_fig and "data" in current_map_fig:
            # Start with the current map figure
            map_fig = go.Figure(data=current_map_fig["data"], layout=current_map_fig["layout"])

            # Remove any existing highlight traces (traces with 'Highlighted' in name)
            map_fig.data = [
                trace
                for trace in map_fig.data
                if not hasattr(trace, "name") or not trace.name.startswith("Highlighted")
            ]

            # Add highlighted polygon if highlight_index is set
            if highlight_index is not None:
                # Get the highlighted geometry
                highlighted_geom = df.iloc[highlight_index].geometry

                # Handle both single polygons and multipolygons
                if highlighted_geom.geom_type == "Polygon":
                    # Single polygon
                    coords = list(highlighted_geom.exterior.coords)
                    lons = [coord[0] for coord in coords]
                    lats = [coord[1] for coord in coords]

                    map_fig.add_trace(
                        go.Scattermapbox(
                            lon=lons,
                            lat=lats,
                            mode="lines",
                            line=dict(width=3, color="red"),
                            fill="toself",
                            fillcolor="rgba(255, 0, 0, 0.2)",
                            name="Highlighted",
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )
                elif highlighted_geom.geom_type == "MultiPolygon":
                    # Multipolygon - add each polygon as a separate trace
                    for i, polygon in enumerate(highlighted_geom.geoms):
                        coords = list(polygon.exterior.coords)
                        lons = [coord[0] for coord in coords]
                        lats = [coord[1] for coord in coords]

                        map_fig.add_trace(
                            go.Scattermapbox(
                                lon=lons,
                                lat=lats,
                                mode="lines",
                                line=dict(width=3, color="red"),
                                fill="toself",
                                fillcolor="rgba(255, 0, 0, 0.2)",
                                name=f"Highlighted_{i}",
                                showlegend=False,
                                hoverinfo="skip",
                            )
                        )
        else:
            # Fallback: create new map if current_map_fig is not available
            map_fig = create_map_plot(df, main_dropdown, highlight_index, colorbar_title=get_axis_title(main_dropdown))

        return upper_fig, lower_fig, cross_upper_fig, cross_lower_fig, map_fig

    # Callback to update map
    @app.callback(Output("map-graph", "figure"), Input("main-dropdown", "value"))
    def update_map(selected_column):
        return create_map_plot(df, selected_column, colorbar_title=get_axis_title(selected_column))

    @app.callback(
        Output("upper-scatter", "figure"),
        Output("lower-scatter", "figure"),
        Input("y-axis-dropdown", "value"),
        Input("x-axis-dropdown", "value"),
    )
    def update_scatter(y_axis_type, x_axis_column):
        if not y_axis_type or not x_axis_column:
            return go.Figure(), go.Figure()

        config = scatter_configs[y_axis_type]
        upper_col = config["upper"]
        lower_col = config["lower"]

        # Calculate consistent ranges for both plots
        x_range, y_range, color_range = calculate_consistent_ranges(df, upper_col, lower_col, x_axis_column)

        # Create scatter plots with consistent ranges
        upper_fig = create_scatter_plot(
            df,
            upper_col,
            x_axis_column,
            x_range=x_range,
            y_range=y_range,
            color_range=color_range,
            x_title=get_axis_title(x_axis_column),
            y_title=get_axis_title(upper_col),
        )

        lower_fig = create_scatter_plot(
            df,
            lower_col,
            x_axis_column,
            x_range=x_range,
            y_range=y_range,
            color_range=color_range,
            x_title=get_axis_title(x_axis_column),
            y_title=get_axis_title(lower_col),
        )

        return upper_fig, lower_fig



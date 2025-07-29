import dash
import geopandas as gpd
import dash_bootstrap_components as dbc
from map_data_presentaiton import create_map_data_layout, create_calloutpus
from dash import html

# Load data
df = gpd.read_parquet('data/combined_data.geoparquet')

# Initialize the Dash app with Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Define the layout using Bootstrap components
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("傅崐萁 2024/2025 立委選舉和罷免案分析", className="text-center mb-4")
        ])
    ]),
] + create_map_data_layout(df), fluid=True)

# Register callbacks
create_calloutpus(app, df)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=7860)
    
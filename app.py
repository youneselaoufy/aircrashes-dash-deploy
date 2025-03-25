# webapp/app.py

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output , dash_table

# Load and prepare data
df = pd.read_csv("data/processed/cleaned_aircrashes_with_geo.csv")
# Combine Year, Month, Day into a proper datetime
df['Date'] = pd.to_datetime(dict(
    year=df['Year'],
    month=df['Month'],
    day=df['Day']
), errors='coerce')

df = df.dropna(subset=['Latitude', 'Longitude', 'Year', 'Fatalities_air'])

# Initialize app
app = Dash(__name__)
app.title = "Air Crashes Map"

# App layout
app.layout = html.Div([
    html.H1("Global Air Crashes (1908–2024)", style={'textAlign': 'center'}),
    # KPI Banner
    html.Div(id='kpi-container', style={
        'display': 'flex',
        'justifyContent': 'space-around',
        'padding': '20px',
        'backgroundColor': '#f9f9f9',
        'borderRadius': '10px',
        'margin': '20px auto',
        'width': '85%',
        'boxShadow': '0 0 8px rgba(0,0,0,0.1)'
    }),

    # Filters
    html.Div([
        html.Label("Year Range:"),
        dcc.RangeSlider(
            id='year-slider',
            min=int(df['Year'].min()),
            max=int(df['Year'].max()),
            step=1,
            value=[2000, 2023],
            marks={y: str(y) for y in range(int(df['Year'].min()), int(df['Year'].max())+1, 10)},
            tooltip={"placement": "bottom", "always_visible": False}
        ),
        html.Br(),

        html.Label("Operator:"),
        dcc.Dropdown(
            id='operator-filter',
            options=[{'label': op, 'value': op} for op in sorted(df['Operator'].dropna().unique())],
            multi=True,
            placeholder="Filter by operator...",
        ),
        html.Br(),

        html.Label("Fatalities Range:"),
        dcc.RangeSlider(
            id='fatalities-slider',
            min=int(df['Fatalities_air'].min()),
            max=int(df['Fatalities_air'].max()),
            value=[0, 300],
            tooltip={"placement": "bottom", "always_visible": False}
        ),
    
    ], style={'width': '85%', 'margin': 'auto'}),

    # Map
    html.Div([
        dcc.Graph(id='crash-map')
    ], style={'padding': '20px'}),
    # Trend Over Time Chart
    html.Div([
        html.H2("Crashes & Fatalities Over Time", style={'textAlign': 'center', 'marginTop': '40px'}),
        dcc.Graph(id='trend-line-chart')
    ], style={'width': '85%', 'margin': 'auto'}),
    # Choropleth Map
    html.Div([
        html.H2("Crashes by Country", style={'textAlign': 'center', 'marginTop': '40px'}),
        dcc.Graph(id='country-choropleth')
    ], style={'width': '85%', 'margin': 'auto'}),

    # Recent Crashes Table
    html.Div([
        html.H2("Recent Crashes", style={'textAlign': 'center', 'marginTop': '40px'}),
        dcc.Loading(
            dash_table.DataTable(
                id='recent-crashes-table',
                columns=[
                    {"name": "Date", "id": "Date"},
                    {"name": "Operator", "id": "Operator"},
                    {"name": "Aircraft", "id": "Aircraft"},
                    {"name": "Location", "id": "Location"},
                    {"name": "Fatalities", "id": "Fatalities_air"}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                page_size=10
            ),
            type="default"
        )
        ], style={'width': '90%', 'margin': 'auto'})
])


@app.callback(
    Output("crash-map", "figure"),
    Input("year-slider", "value"),
    Input("operator-filter", "value"),
    Input("fatalities-slider", "value")
)
def update_map(year_range, selected_operators, fatalities_range):
    # Load data
    df = pd.read_csv("data/processed/cleaned_aircrashes_with_geo.csv")

    # Map month names to numeric values
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].map(month_map)

    # Drop invalid rows
    df = df.dropna(subset=['Year', 'Month', 'Day', 'Latitude', 'Longitude', 'Fatalities_air'])

    # Rebuild Date column
    df['Date'] = pd.to_datetime(dict(
        year=df['Year'].astype(int),
        month=df['Month'].astype(int),
        day=df['Day'].astype(int)
    ), errors='coerce')
    df['Date'] = df['Date'].dt.strftime("%Y-%m-%d")

    # Apply filters
    filtered = df[
        (df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1]) &
        (df["Fatalities_air"] >= fatalities_range[0]) & (df["Fatalities_air"] <= fatalities_range[1])
    ]

    if selected_operators:
        filtered = filtered[filtered["Operator"].isin(selected_operators)]

    # Build interactive map
    fig = px.scatter_mapbox(
        filtered,
        lat="Latitude",
        lon="Longitude",
        hover_name="Operator",
        hover_data={
            "Date": True,
            "Aircraft": True,
            "Fatalities_air": True,
            "Location": True,
            "Latitude": False,
            "Longitude": False
        },
        size="Fatalities_air",
        color="Fatalities_air",
        color_continuous_scale="Reds",
        size_max=15,
        zoom=1,
        height=700
    )

    fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
    return fig



@app.callback(
    Output('kpi-container', 'children'),
    Input("year-slider", "value"),
    Input("operator-filter", "value"),
    Input("fatalities-slider", "value")
)
def update_kpis(year_range, selected_operators, fatalities_range):
    df = pd.read_csv("data/processed/cleaned_aircrashes_with_geo.csv")

    # Month mapping
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].map(month_map)

    df = df.dropna(subset=['Year', 'Month', 'Day', 'Latitude', 'Longitude', 'Fatalities_air'])

    df['Date'] = pd.to_datetime(dict(
        year=df['Year'].astype(int),
        month=df['Month'].astype(int),
        day=df['Day'].astype(int)
    ), errors='coerce')

    # Filter
    filtered = df[
        (df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1]) &
        (df["Fatalities_air"] >= fatalities_range[0]) & (df["Fatalities_air"] <= fatalities_range[1])
    ]

    if selected_operators:
        filtered = filtered[filtered["Operator"].isin(selected_operators)]

    total_crashes = len(filtered)
    total_fatalities = int(filtered['Fatalities_air'].sum())
    avg_fatalities = round(filtered['Fatalities_air'].mean(), 1) if total_crashes else 0
    worst_crash = int(filtered['Fatalities_air'].max()) if total_crashes else 0

    def card(title, value):
        return html.Div([
            html.H4(title, style={'marginBottom': '5px'}),
            html.H2(f"{value}", style={'color': '#D9534F' if 'Fatalities' in title else '#333'})
        ], style={
            'padding': '10px 20px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'textAlign': 'center',
            'boxShadow': '0 0 5px rgba(0,0,0,0.1)'
        })

    return [
        card("Total Crashes", total_crashes),
        card("Total Fatalities", total_fatalities),
        card("Avg. Fatalities/Crash", avg_fatalities),
        card("Worst Crash Fatalities", worst_crash)
    ]


@app.callback(
    Output('trend-line-chart', 'figure'),
    Input("year-slider", "value"),
    Input("operator-filter", "value"),
    Input("fatalities-slider", "value")
)
def update_trend_line(year_range, selected_operators, fatalities_range):
    df = pd.read_csv("data/processed/cleaned_aircrashes_with_geo.csv")

    # Month name → number
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].map(month_map)

    # Drop missing data
    df = df.dropna(subset=['Year', 'Month', 'Day', 'Latitude', 'Longitude', 'Fatalities_air'])

    # Filters
    filtered = df[
        (df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1]) &
        (df["Fatalities_air"] >= fatalities_range[0]) & (df["Fatalities_air"] <= fatalities_range[1])
    ]
    if selected_operators:
        filtered = filtered[filtered["Operator"].isin(selected_operators)]

    # Group by year
    yearly = filtered.groupby("Year").agg({
        "Fatalities_air": "sum",
        "Aircraft": "count"  # just to count rows (crashes)
    }).reset_index().rename(columns={"Aircraft": "Total_Crashes", "Fatalities_air": "Total_Fatalities"})

    # Build figure
    fig = px.line(yearly, x="Year", y=["Total_Crashes", "Total_Fatalities"],
                  labels={"value": "Count", "variable": "Metric"},
                  title="Yearly Trends of Crashes and Fatalities")

    fig.update_layout(
        template="plotly_white",
        margin={"r": 20, "t": 40, "l": 20, "b": 40},
        legend_title_text=""
    )

    return fig

@app.callback(
    Output('country-choropleth', 'figure'),
    Input("year-slider", "value"),
    Input("operator-filter", "value"),
    Input("fatalities-slider", "value")
)
def update_choropleth(year_range, selected_operators, fatalities_range):
    df = pd.read_csv("data/processed/cleaned_aircrashes_with_geo.csv")

    # Month mapping
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].map(month_map)

    df = df.dropna(subset=['Year', 'Month', 'Day', 'Latitude', 'Longitude', 'Fatalities_air', 'Country/Region'])

    df['Date'] = pd.to_datetime(dict(
        year=df['Year'].astype(int),
        month=df['Month'].astype(int),
        day=df['Day'].astype(int)
    ), errors='coerce')

    # Filter
    filtered = df[
        (df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1]) &
        (df["Fatalities_air"] >= fatalities_range[0]) & (df["Fatalities_air"] <= fatalities_range[1])
    ]

    if selected_operators:
        filtered = filtered[filtered["Operator"].isin(selected_operators)]

    # Group by country
    grouped = filtered.groupby("Country/Region").agg({
        "Fatalities_air": "sum",
        "Aircraft": "count"
    }).reset_index().rename(columns={"Aircraft": "Total_Crashes", "Fatalities_air": "Total_Fatalities"})

    # Choropleth
    fig = px.choropleth(
        grouped,
        locations="Country/Region",
        locationmode="country names",
        color="Total_Crashes",  # Can also switch to "Total_Fatalities"
        hover_name="Country/Region",
        color_continuous_scale="Reds",
        title="Total Crashes by Country"
    )

    fig.update_layout(margin={"r":0, "t":40, "l":0, "b":0})

    return fig


@app.callback(
    Output("recent-crashes-table", "data"),
    Input("year-slider", "value"),
    Input("operator-filter", "value"),
    Input("fatalities-slider", "value")
)
def update_table(year_range, selected_operators, fatalities_range):
    df = pd.read_csv("data/processed/cleaned_aircrashes_with_geo.csv")

    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].map(month_map)

    df = df.dropna(subset=['Year', 'Month', 'Day', 'Latitude', 'Longitude', 'Fatalities_air'])

    df['Date'] = pd.to_datetime(dict(
        year=df['Year'].astype(int),
        month=df['Month'].astype(int),
        day=df['Day'].astype(int)
    ), errors='coerce')

    filtered = df[
        (df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1]) &
        (df["Fatalities_air"] >= fatalities_range[0]) & (df["Fatalities_air"] <= fatalities_range[1])
    ]

    if selected_operators:
        filtered = filtered[filtered["Operator"].isin(selected_operators)]

    filtered['Date'] = filtered['Date'].dt.strftime("%Y-%m-%d")

    # Show most recent first
    filtered = filtered.sort_values(by="Date", ascending=False)

    return filtered[["Date", "Operator", "Aircraft", "Location", "Fatalities_air"]].head(20).to_dict("records")




# Run
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)


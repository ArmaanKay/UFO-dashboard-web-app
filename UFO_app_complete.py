import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# Load the data
df = pd.read_csv('/Users/armaankhokhar/Documents/Dashboards/UFO_dashboard_complete/UFO_encounters_complete.csv', 
                 parse_dates=["Date_time", 'date_documented', 'month_year'])

# Prepare data for the Encounters per Country Over Time part
# Grouping data by 'Country', 'month_year', 'Continent', and counting encounters
encounters_df = df.groupby(['Country', 'month_year', 'year','Continent'])['encounter_id'].count().reset_index()
encounters_df = encounters_df.rename(columns={"encounter_id": "encounters"})

# Dark theme URL from Dash Bootstrap Components
dark_theme_url = dbc.themes.DARKLY

# Orbitron font URL from Google Fonts
orbitron_font_url = 'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap'

# Combine both URLs in the external_stylesheets list
external_stylesheets = [dark_theme_url, orbitron_font_url]

# Initialize the Dash app with both the dark theme and Orbitron font
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Define default countries for the line graph
default_countries = ["Australia", "Canada", "Netherlands", "United Kingdom"]

# App layout
app.layout = html.Div([
    html.H1("Close Encounters Dashboard", 
            style={
                'textAlign': 'center', 
                'marginTop': '20px', 
                'marginBottom': '20px',
                'color': 'green',
                'font-family': 'Orbitron, sans-serif'  # Using Orbitron font
            }
    ),

    # Part 3: UFO Map App Layout
    html.H1("UFO Sightings Map"),
    html.Div([
        dcc.Graph(id='ufo-map'),
        html.Label('Select Year Range:'),
        dcc.RangeSlider(
            id='map-year-slider',  # Changed ID to avoid conflict
            min=df['year'].min(),
            max=df['year'].max(),
            value=[df['year'].min(), df['year'].max()],
            marks={str(year): str(year) for year in df['year'].unique()},
            step=None
        ),
        html.Label('Select Hour Range:'),
        dcc.RangeSlider(
            id='hour-slider',
            min=0,
            max=23,
            value=[0, 23],
            marks={str(hour): str(hour) for hour in range(24)},
            step=1
        ),
        html.Button('Play/Pause Animation', id='play-pause-button', n_clicks=0),
        dcc.Interval(
            id='interval-component',
            interval=1*1000,  # in milliseconds
            n_intervals=0,
            disabled=True  # Initially disabled
        )
    ]),

    # Part 1: UFO Encounter Analysis Layout
    html.H1("UFO Encounter Analysis"),
    html.Div([
        html.Label("Select X-axis Category:"),
        dcc.Dropdown(
            id='xaxis-column',
            options=[
                {'label': 'Hour', 'value': 'hour'},
                {'label': 'Day', 'value': 'day'},
                {'label': 'Month', 'value': 'month'},
                {'label': 'Season', 'value': 'Season'},
                {'label': 'Year', 'value': 'year'},
                {'label': 'UFO Shape', 'value': 'UFO_shape'},
                {'label': 'Continent', 'value': 'Continent'}
            ],
            style={'color': 'black'},
            value='month'  # default value
        )
    ]),
    html.Div([
        html.Label("Select Continent(s):"),
        dcc.Dropdown(
            id='continent-column',
            # Assuming df is your DataFrame with a 'Continent' column
            options=[{'label': continent, 'value': continent} for continent in df['Continent'].unique()],
            value=df['Continent'].unique().tolist(),  # default to all continents
            multi=True  # allow multiple selections
        )
    ]),
    dcc.Graph(id='ufo-graphic'),

    # Part 2: Encounters per Country Over Time Layout
    html.H1('Encounters per Country Over Time'),
    html.Div([
        html.Label("Select Year Range:"),
        dcc.RangeSlider(
            id='year-slider',
            min=df['year'].min(),
            max=df['year'].max(),
            value=[df['year'].min(), df['year'].max()],
            marks={year: str(year) for year in range(df['year'].min(), df['year'].max() + 1)},
            step=1
        )
    ], style={'padding': '20px', 'maxWidth': '90%'}),  # Adjusted range slider width

    html.Div([
        html.Label("Select Countries:"),
        html.Div([
            dcc.Dropdown(
                id=f"country-dropdown-{i}",
                options=[{"label": country, "value": country} for country in df['Country'].unique()],
                value=default_countries[i] if i < len(default_countries) else None
            ) for i in range(4)  # Adjust to use default_countries
        ], style={'padding': '10px', 'maxWidth': '400px', 'color': 'black'})
    ]),
    
    dcc.Graph(id="country-graph"),
])

# Define the callback for UFO Encounter Analysis
@app.callback(
    Output('ufo-graphic', 'figure'),
    [Input('xaxis-column', 'value'),
     Input('continent-column', 'value')]
)
def update_ufo_graph(xaxis_value, continent_value):
    # Filter the dataframe based on selected continents
    filtered_df = df[df['Continent'].isin(continent_value)]

    # Group by the selected x-axis and country after filtering
    grouped_df = filtered_df.groupby([xaxis_value, 'Country']).size().reset_index(name='counts')

    # Creating the bar chart with colors based on country
    fig = px.bar(grouped_df, x=xaxis_value, y='counts', color='Country',
                 labels={'counts': 'Number of Encounters', 'Country': 'Country'})
    fig.update_layout(transition_duration=500)
    return fig

# Define the callback for Encounters per Country Over Time
@app.callback(
    Output("country-graph", "figure"), 
    [Input(f"country-dropdown-{i}", "value") for i in range(4)] + 
    [Input('year-slider', 'value')]
)
def update_country_graph(*args):
    selected_countries = args[:4]  # First four arguments are countries
    year_range = args[4]  # Fifth argument is the year range

    # Filter data based on selected countries and year range
    mask = (encounters_df['Country'].isin(selected_countries)) & \
           (encounters_df['year'] >= year_range[0]) & \
           (encounters_df['year'] <= year_range[1])
    filtered_df = encounters_df[mask]

    # Creating the line chart
    fig = px.line(filtered_df, 
                  x="month_year", y="encounters", color='Country',
                  title='Encounters per Country Over Time')
    return fig

# Callback for the animation of the map
@app.callback(
    Output('map-year-slider', 'value'),  # Updated to 'map-year-slider'
    [Input('interval-component', 'n_intervals'), Input('play-pause-button', 'n_clicks')],
    [State('map-year-slider', 'value'), State('map-year-slider', 'max')]  # Updated to 'map-year-slider'
)
def update_slider(n_intervals, n_clicks, current_value, max_year):
    # Check if the button has been clicked an even number of times (indicating a pause)
    if n_clicks % 2 == 0:
        raise dash.exceptions.PreventUpdate
    else:
        if current_value[1] < max_year:
            return [current_value[0], current_value[1] + 1]
        else:
            return [current_value[0], df['year'].min()]

# Callback to enable/disable the interval component for animation
@app.callback(
    Output('interval-component', 'disabled'),
    [Input('play-pause-button', 'n_clicks')],
    [State('interval-component', 'disabled')]
)
def toggle_animation(n_clicks, is_disabled):
    if n_clicks % 2 == 0:
        return True
    else:
        return False

# Callback to update the map based on the sliders
@app.callback(
    Output('ufo-map', 'figure'),
    [Input('map-year-slider', 'value'), Input('hour-slider', 'value')]
)
def update_map(selected_years, selected_hours):
    # Logic to filter df based on selected_years and selected_hours
    filtered_df = df[(df['year'] >= selected_years[0]) & (df['year'] <= selected_years[1])]
    filtered_df = filtered_df[(filtered_df['hour'] >= selected_hours[0]) & (filtered_df['hour'] <= selected_hours[1])]

    # Create the map figure
    fig = px.scatter_mapbox(filtered_df, lat="latitude", lon="longitude",
                            color="hour", hover_name="Date_time",
                            hover_data=["Country", "UFO_shape", "Description"],
                            color_continuous_scale=px.colors.cyclical.IceFire,
                            size_max=15, zoom=3, mapbox_style="open-street-map")
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
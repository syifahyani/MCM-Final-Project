import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json
import requests

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

df = pd.read_csv('https://raw.githubusercontent.com/syifahyani/MCM-Final-Project/refs/heads/main/assets/Malaysia%20Crime%20District.csv')
df['Year'] = pd.to_numeric(df['Incident Date'], errors='coerce')

states = df['State'].unique()
categories = df['Crime Category'].unique()
years = df['Year'].unique()

full_df = pd.MultiIndex.from_product([states, categories, years], names=['State', 'Crime Category', 'Year']).to_frame(index=False)
df = pd.merge(full_df, df, on=['State', 'Crime Category', 'Year'], how='left').fillna(0)

crime_type_data = df.groupby('Crime Type')['Reported Crimes'].sum().reset_index()

geojson_url = "https://raw.githubusercontent.com/syifahyani/MCM-Final-Project/refs/heads/main/assets/malaysia_state.geojson"
states_json = requests.get(geojson_url).json()

def create_map(selected_state=None):
    df_grouped = df.groupby('State', as_index=False)['Reported Crimes'].sum()
    min_crimes = df_grouped['Reported Crimes'].min()
    max_crimes = df_grouped['Reported Crimes'].max()

    if selected_state and selected_state != "All":
        df_filtered = df[df['State'] == selected_state]
        df_grouped_filtered = df_filtered.groupby('State', as_index=False)['Reported Crimes'].sum()
        fig = px.choropleth(df_grouped_filtered, geojson=states_json, locations="State", color="Reported Crimes",
                            featureidkey="properties.name", template='plotly_white',
                            range_color=[min_crimes, max_crimes])
    else:
        fig = px.choropleth(df_grouped, geojson=states_json, locations="State", color="Reported Crimes",
                            featureidkey="properties.name", template='plotly_white',
                            range_color=[min_crimes, max_crimes])

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")

    return fig

def create_scatter_plot():
    fig = px.scatter(df, x='Reported Crimes', y='State', animation_frame='Year', animation_group='State',
                     size='Reported Crimes', color='Crime Category', hover_name='State', facet_col='Crime Category',
                     log_x=False, size_max=45)

    # Update layout for all subplots
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    # Update x and y axes for all subplots
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='lightgray',
    )

    # Get all unique states
    all_states = df['State'].unique()

    # Update y-axes for all subplots
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='lightgray',
        tickmode='array',
        tickvals=list(range(len(all_states))),
        ticktext=all_states,
        autorange="reversed",  # Reverse the y-axis to show states from top to bottom
    )

    # Update subplot titles and adjust margins
    fig.update_layout(
        margin=dict(l=150, r=20, t=50, b=50),  # Increase left margin to accommodate state names
        annotations=[
            dict(
                x=ann['x'], y=ann['y'],
                text=ann['text'],
                font=dict(size=12),
                showarrow=False,
                xref='paper', yref='paper'
            ) for ann in fig.layout.annotations
        ]
    )

    return fig

def create_bar_chart(selected_crime_types):
    filtered_df = df[df['Crime Type'].isin(selected_crime_types)]
    bar_data = filtered_df.groupby(['State', 'Crime Type'])['Reported Crimes'].sum().reset_index()
    
    fig = px.bar(bar_data, 
                 x='State', 
                 y='Reported Crimes', 
                 color='Crime Type', 
                 title='Total Reported Crimes by State and Crime Type',
                 barmode='group')

    fig.update_layout(
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

app.layout = dbc.Container([

    dbc.Row([
        dbc.Col([
            html.H2("Crime Data Overview"),
            html.P("This dataset contains information about reported crimes across various states in Malaysia. "
                   "The data includes the number of reported crimes by category (e.g., Assault, Property) for each state. "
                   "The visualizations below will help explore the geographical distribution of crimes and identify states "
                   "with higher crime rates."),
            html.P("By selecting a state from the dropdown below, you can filter the map to display crime data specific "
                   "to that region, or you can view the overall crime distribution across the entire country.")
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            html.Label("Select State:"),
            dcc.Dropdown(
                id='state-dropdown',
                options=[{'label': 'All', 'value': 'All'}] + 
                        [{'label': state, 'value': state} for state in df['State'].unique()],
                value='All',
                clearable=False
            )
        ], width=4),
    ]),

    dbc.Row([    
        dbc.Col(dcc.Graph(id='choropleth-map'), width=12)
    ]),

    html.Hr(),

    dbc.Row([
        dbc.Col(html.H2("Crime Trends Over Time"), width=12)
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='scatter-plot'), width=12)
    ]),

    html.Hr(),

    dbc.Row([
        dbc.Col(html.H2("Total Crimes by State and Crime Type"), width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Checklist(
                id='crime-type-checklist',
                options=[{'label': 'All', 'value': 'All'}] + 
                        [{'label': crime, 'value': crime} for crime in df['Crime Type'].unique()],
                value=['All'],
                labelStyle={'display': 'inline-block', 'margin-right': '15px', 'margin-bottom': '10px'},
                inputStyle={"margin-right": "5px"},
                className="mb-3"
            )
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-chart'), width=12)
    ])
])

@app.callback(
    Output('choropleth-map', 'figure'),
    [Input('state-dropdown', 'value')]
)
def update_map(selected_state):
    return create_map(selected_state)

@app.callback(
    Output('scatter-plot', 'figure'),
    Input('scatter-plot', 'id')
)
def update_scatter_plot(_):
    return create_scatter_plot()

@app.callback(
    Output('bar-chart', 'figure'),
    [Input('crime-type-checklist', 'value')]
)
def update_bar_chart(selected_crime_types):
    if 'All' in selected_crime_types or not selected_crime_types:
        selected_crime_types = df['Crime Type'].unique()
    return create_bar_chart(selected_crime_types)

@app.callback(
    Output('crime-type-checklist', 'value'),
    Input('crime-type-checklist', 'value')
)
def update_checklist(selected_values):
    if not selected_values:
        return ['All']
    if 'All' in selected_values and len(selected_values) > 1:
        return [val for val in selected_values if val != 'All']
    return selected_values

if __name__ == "__main__":
    app.run_server(debug=True)

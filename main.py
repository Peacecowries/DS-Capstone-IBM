import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

df = pd.read_csv('dataset_part_2.csv')
df['Date'] = pd.to_datetime(df['Date'])
df.dropna(axis=1, inplace=True)
corr = df[['Date', 'BoosterVersion', 'PayloadMass', 'Orbit',
       'LaunchSite', 'Flights', 'Class']]
print(df.PayloadMass.max())
app = Dash(__name__)

app.layout = html.Div(style={'display': 'flex', 'flexFlow': 'column'}, children=[
    html.H1('SpaceX Falcon 9 Visualisation'),

    html.Div(style={'display': 'flex', 'flexFlow': 'row'}, children=[
        dcc.Dropdown(
            id='orbit-dropdown',
            options=[{'label': i, 'value': i} for i in df['Orbit'].unique()],
            value=df['Orbit'].unique(),
            multi=True,
            placeholder='Select orbits'
        ),
        dcc.Dropdown(
            id='launchsite-dropdown',
            options=[{'label': i, 'value': i} for i in df['LaunchSite'].unique()],
            value=df['LaunchSite'].unique(),
            multi=True,
            placeholder='Select launch sites'
        ),
        dcc.Checklist(
            id='year-checkbox',
            options=[{'label': 'All Years', 'value': True}]
        ),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': i, 'value': i} for i in df['Date'].dt.year.unique()],
            value=df['Date'].dt.year.unique(),
            multi=True,
            placeholder='Select years'
        ),
        dcc.RangeSlider(
            id='payloadmass-slider',
            min=df['PayloadMass'].min(),
            max=df['PayloadMass'].max(),
            step=100,
            value=[df['PayloadMass'].min(), df['PayloadMass'].max()]
        ),
    ]),

    html.Div(style={'display': 'flex', 'flexFlow': 'row'}, children=[
        dcc.Graph(id='success-piechart'),
        dcc.Graph(id='heatmap-numeric'),
    ]),

    html.Div(style={'display': 'flex', 'flexFlow': 'row'}, children=[
        dcc.Graph(id='usa-heatmap'),
        dcc.Graph(id='timeseries-plot'),
    ]),

    html.Div(style={'display': 'flex', 'flexFlow': 'row'}, children=[
        dcc.Graph(id='orbit-barchart'),
    ]),
])


@app.callback(
    Output('success-piechart', 'figure'),
    Output('heatmap-numeric', 'figure'),
    Output('usa-heatmap', 'figure'),
    Output('timeseries-plot', 'figure'),
    Output('orbit-barchart', 'figure'),
    Input('orbit-dropdown', 'value'),
    Input('launchsite-dropdown', 'value'),
    Input('year-checkbox', 'value'),
    Input('year-dropdown', 'value'),
    Input('payloadmass-slider', 'value'),
)
def update_graphs(orbit_values, launchsite_values, year_checkbox, year_values, payload_values):
    # Filtering data based on dropdowns and slider
    dff = df[df['Orbit'].isin(orbit_values)]
    dff = dff[dff['LaunchSite'].isin(launchsite_values)]
    dff = dff[(dff['PayloadMass'] >= payload_values[0]) & (dff['PayloadMass'] <= payload_values[1])]
    if not year_checkbox:
        dff = dff[dff['Date'].dt.year.isin(year_values)]

    # Pie Chart for success rate
    success_counts = dff['Class'].value_counts()
    success_pie = px.pie(values=success_counts.values, names=['Failure', 'Success'])

    # Heatmap for all numeric columns correlation
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=dff.corr(numeric_only=True),
        x=dff.columns,
        y=dff.columns,
        colorscale='Viridis'))

    # Interactive USA Heatmap for launch site success rate
    launch_success_rate = dff.groupby('LaunchSite')[['Class','Latitude','Longitude']].mean().reset_index()
    usa_heatmap = px.scatter_geo(launch_success_rate,
                                 lat='Latitude',
                                 lon='Longitude',
                                 color='Class',
                                 color_continuous_scale="Viridis",
                                 range_color=(0, 1),
                                 scope="usa",
                                 labels={'Class': 'success rate'})
    # TimeSeries Plot for the success rate over years hued by Launch Sites
    success_rate_time = dff.groupby(['Date', 'LaunchSite'])['Class'].mean().reset_index()
    timeseries_plot = px.line(success_rate_time, x='Date', y='Class', color='LaunchSite')

    # Bar Chart for orbits success rate hued by launch sites
    orbit_success_rate = dff.groupby(['Orbit', 'LaunchSite'])['Class'].mean().reset_index()
    orbit_barchart = px.bar(orbit_success_rate, x='Orbit', y='Class', color='LaunchSite')

    return success_pie, heatmap_fig, usa_heatmap, timeseries_plot, orbit_barchart


if __name__ == '__main__':
    app.run_server(debug=True)

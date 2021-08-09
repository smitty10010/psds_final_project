# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import os

try:
    from dotenv import load_dotenv
except ImportError:
    from pip._internal import main as pip
    pip(['install', 'python-dotenv'])
    from dotenv import load_dotenv
try:
    import psycopg2
except ImportError:
    from pip._internal import main as pip
    pip(['install', 'psycopg2'])
    import psycopg2

import time
import sqlalchemy
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_deck
import plotly.express as px
import pydeck as pdk
import pandas as pd

load_dotenv(
    dotenv_path='./.env')
db = os.getenv('DB')
mapToken = os.getenv('mapbox_Token')

sales_sql = sqlalchemy.text("""SELECT s2.buyer,
s2.seller,
s2.weapon,
s2.weapon_description,
coalesce(s2.number_delivered,0),
s2.delivery_year,
ST_Y(ST_centroid(s.seller_location)) AS seller_center_lat,
ST_X(ST_Centroid(s.seller_location)) AS seller_center_lon,
ST_Y(ST_centroid(s.buyer_location)) AS buyer_center_lat,
ST_X(ST_Centroid(s.buyer_location)) AS buyer_center_lon
FROM
(SELECT *,geo1.geom AS seller_location,geo2.geom AS buyer_location
 FROM sipri
 JOIN borders geo1 ON sipri.seller = geo1.admin
 JOIN borders geo2 ON sipri.buyer = geo2.admin
 WHERE CASE
 WHEN LENGTH(delivery_year) > 4 THEN CAST(RIGHT(delivery_year, 4) AS INTEGER)
 ELSE CAST(delivery_year AS INTEGER)
 END > 2000
 AND weapon_description IN('Armed UAV')) s
JOIN sipri s2 ON s.buyer = s2.buyer
WHERE s.buyer = s2.buyer
AND s.seller = s2.seller
AND s2.weapon_description IN('ASM',
                             'Guided bomb',
                             'Anti-tank missile',
                             'Armed UAV')
ORDER BY s2.seller,
s2.buyer;""")

strike_sql = sqlalchemy.text("""SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Drone Strike'
       END type_of_strike,
       acled.fatalities,acled.latitude,acled.longitude,acled.country,acled.event_date,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop
FROM acled
CROSS JOIN LATERAL
    (SELECT name,
            geom,
            cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country IN ('Afghanistan',
                  'Syria',
                  'Iraq',
                  'Yemen',
                  'Pakistan',
                  'Mali',
                  'Turkey',
                  'Ukraine',
                  'Azerbaijan',
                  'Saudi Arabia',
                  'Palestine',
                  'Armenia',
                  'Libya',
                  'Burkina Faso',
                  'Somalia',
                  'Egypt',
                  'Israel',
                  'Lebanon',
                  'Venezuela',
                  'United Arab Emirates',
                  'Nigeria',
                  'South Sudan')
    AND year > 2000
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND notes LIKE '%drone%'
UNION
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Air Strike'
       END type_of_strike,
       acled.fatalities,acled.latitude,acled.longitude,acled.country,acled.event_date,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop
FROM acled
CROSS JOIN LATERAL
    (SELECT name,
            geom,
            cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country IN ('Afghanistan',
                  'Syria',
                  'Iraq',
                  'Yemen',
                  'Pakistan',
                  'Mali',
                  'Turkey',
                  'Ukraine',
                  'Azerbaijan',
                  'Saudi Arabia',
                  'Palestine',
                  'Armenia',
                  'Libya',
                  'Burkina Faso',
                  'Somalia',
                  'Egypt',
                  'Israel',
                  'Lebanon',
                  'Venezuela',
                  'United Arab Emirates',
                  'Nigeria',
                  'South Sudan')
    AND year > 2000
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND notes NOT ILIKE ALL (ARRAY['%drone%'])
ORDER BY event_date;""")

df = pd.read_sql_query(sales_sql, db)

strikes = pd.read_sql_query(strike_sql, db)

drone = strikes.query('type_of_strike == "Drone Strike"')

GREEN_RGB = [0, 255, 0, 40]
RED_RGB = [240, 100, 0, 40]

# Specify a deck.gl ArcLayer
arc_layer = pdk.Layer(
    "ArcLayer",
    data=df,
    get_width=1,
    get_source_position=["seller_center_lon", "seller_center_lat"],
    get_target_position=["buyer_center_lon", "buyer_center_lat"],
    get_tilt=15,
    get_source_color=RED_RGB,
    get_target_color=GREEN_RGB,
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.data_utils.compute_view(
    points=df[["buyer_center_lon", "buyer_center_lat"]], view_proportion=1)

""" view_state = pdk.ViewState(
    latitude=0, longitude=-0, bearing=0, pitch=35, zoom=zoom_level,
)"""


r = pdk.Deck(layers=[arc_layer], initial_view_state=view_state,
             api_keys={'mapbox': mapToken}, map_provider='mapbox', tooltip=True)

r = r.to_json()

heat_layer = pdk.Layer(
    "HeatmapLayer",
    data=drone,
    get_position=["longitude", "latitude"],
    # aggregation="'SUM'",
    # color_range=COLOR_BREWER_BLUE_SCALE,
    # threshold=1,
    # get_weight="fatalities",
    # pickable=True,
)
print('1')
heat_view_state = pdk.data_utils.compute_view(
    points=drone[["longitude", "latitude"]])
print('2')
heat_r = pdk.Deck(layers=[heat_layer], initial_view_state=heat_view_state,
                  api_keys={'mapbox': mapToken}, map_provider='mapbox')
print('3')

#heat_r = heat_r.to_json()
print('4')
#df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/c78bf172206ce24f77d6363a2d754b59/raw/c353e8ef842413cae56ae3920b8fd78468aa4cb2/usa-agricultural-exports-2011.csv')

#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dcc.Store(id="store"),
        html.H1("Global Armed Drone Sales and Drone Strikes Dashboard"),
        html.Hr(),
        dbc.Tabs(
            [
                dbc.Tab(label='Armed Drone Sales', tab_id='drone-sales'),
                dbc.Tab(label='Global Drone Strikes vs Manned Airstrikes',
                        tab_id='drone-strikes'),
            ],
            id='tabs', active_tab='drone-sales'),
        html.Div(id="tab-content", className="p-4"),
    ]
)

""" app.layout = dbc.Container(
    [
        html.H1("Global Armed Drone Sales and Drone Strikes Dashboard"),
        html.Hr(),
        dcc.Dropdown(
            id='yaxis-column',
            options=[{'label': i, 'value': i} for i in df.seller.unique()],
            value=['China', 'Iran', 'Turkey',
                   'United Arab Emirates', 'United States of America'],
            multi=True),
        dbc.Button(
            "Submit",
            color="primary",
            block=True,
            id="submit-button",
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Card(dcc.Loading(
                    id="loading-1",
                    type="default",
                    children=dcc.Graph(id='graph')
                ), body=True, style={"height": "calc(95vh - 215px)"},), md=6),
                dbc.Col(dbc.Card(
                    dash_deck.DeckGL(
                        data=r, id="deck-gl", mapboxKey=mapToken, tooltip=True,
                    ), body=True, style={"height": "calc(95vh - 215px)"},), md=6),
            ],
            align="center",
        ),
    ]
) """

""" app.layout = html.Div(children=[
    dcc.Dropdown(
        id='yaxis-column',
        options=[{'label': i, 'value': i} for i in df.seller.unique()],
        value=['China', 'Iran', 'Turkey',
               'United Arab Emirates', 'United States'],
        multi=True),
    html.Button(id='submit-button', n_clicks=0, children='Submit'),
    dcc.Loading(
        id="loading-1",
        type="default",
        children=dcc.Graph(id='graph')
    ),
    html.Div(
        dash_deck.DeckGL(
            r.to_json(), id="deck-gl", tooltip=TOOLTIP_TEXT, mapboxKey=mapToken
        ))
]) """


@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'), Input('store', 'data')],
)
def render_tab_content(active_tab, data):
    if active_tab == 'drone-sales':
        return [dcc.Dropdown(
            id='yaxis-column',
            options=[{'label': i, 'value': i} for i in df.seller.unique()],
            value=['China', 'Iran', 'Turkey',
                   'United Arab Emirates', 'United States of America'],
            multi=True),
            dbc.Button(
            "Submit",
            color="primary",
            block=True,
            id="submit-button",
            className="mb-3",
        ),
            dbc.Row(
            [
                dbc.Col(dbc.Card(dcc.Loading(
                    id="loading-1",
                    type="default",
                    children=dcc.Graph(id='graph')
                ), body=True, style={"height": "calc(95vh - 215px)"},), md=6),
                dbc.Col(dbc.Card(
                    dash_deck.DeckGL(
                        data=r, id="deck-gl", mapboxKey=mapToken, tooltip=True,
                    ), body=True, style={"height": "calc(95vh - 215px)"},), md=6),
            ],
            align="center",
        ), ]
    elif active_tab == 'drone-strikes':
        return [dcc.Dropdown(
            id='strike-yaxis-column',
            options=[{'label': i, 'value': i}
                for i in strikes.country.unique()],
            value=['Afghanistan', 'Syria', 'Iraq', 'Yemen', 'Pakistan', 'Mali',
                   'Turkey', 'Ukraine', 'Azerbaijan', 'Saudi Arabia', 'Palestine',
                   'Armenia', 'Libya', 'Burkina Faso', 'Somalia', 'Egypt', 'Israel',
                   'Lebanon', 'Venezuela', 'United Arab Emirates', 'Nigeria',
                   'South Sudan'],
            multi=True),
            dbc.Button(
            "Submit",
            color="primary",
            block=True,
            id="strike-submit-button",
            className="mb-3",
        ),
            dbc.Row(
            [
                dbc.Col(dbc.Card(dcc.Loading(
                    id="strike-loading-1",
                    type="default",
                    children=dcc.Graph(id='strike-graph')
                ), body=True, style={"height": "calc(95vh - 215px)"},), md=6),
                dbc.Col(dbc.Card(
                    dash_deck.DeckGL(
                        data=heat_r, id="strike-deck-gl", mapboxKey=mapToken, tooltip=True,
                    ), body=True, style={"height": "calc(95vh - 215px)"},), md=6),
            ],
            align="center",
        ), ]


@app.callback(
    Output("graph", "figure"),
    #Output('deck-gl', 'data'),
    #Output('graph', 'figure'),
    Input('submit-button', 'n_clicks'),
    State('yaxis-column', 'value'))
def update_graph(n_clicks, yaxis_column_name):
    clicks = n_clicks

    dff = df[df['seller'].isin(yaxis_column_name)]

    dff = dff.query("weapon_description == 'Armed UAV'")

    fig = px.scatter(dff, x='buyer',
                     y='seller', color='weapon', size='coalesce')

    fig.update_layout(transition_duration=500)

    return fig


@app.callback(
    Output('deck-gl', 'data'),
    Input('submit-button', 'n_clicks'),
    State('yaxis-column', 'value'))
def update_map(n_clicks, yaxis_column_name):
    clicks = n_clicks

    dff = df[df['seller'].isin(yaxis_column_name)]

    updated_layer = pdk.Layer(
        "ArcLayer",
        data=dff,
        get_width=1,
        get_source_position=["seller_center_lon", "seller_center_lat"],
        get_target_position=["buyer_center_lon", "buyer_center_lat"],
        get_tilt=15,
        get_source_color=RED_RGB,
        get_target_color=GREEN_RGB,
        pickable=True,
        auto_highlight=True,
    )
    new_view_state = pdk.data_utils.compute_view(
        points=dff[["buyer_center_lon", "buyer_center_lat"]], view_proportion=1)

    r = pdk.Deck(layers=updated_layer, initial_view_state=new_view_state,
                 api_keys={'mapbox': mapToken}, map_provider='mapbox', tooltip=True)

    return r.to_json()


@app.callback(
    Output("strike-graph", "figure"),
    #Output('deck-gl', 'data'),
    #Output('graph', 'figure'),
    Input('strike-submit-button', 'n_clicks'),
    State('strike-yaxis-column', 'value'))
def update_graph(n_clicks, strike_yaxis_column_name):
    clicks = n_clicks

    dff = strikes[strikes['country'].isin(strike_yaxis_column_name)]

    fig = px.box(dff, x='type_of_strike',
                 y='fatalities')

    fig.update_layout(transition_duration=500)

    return fig


@app.callback(
    Output('strike-deck-gl', 'data'),
    Input('strike-submit-button', 'n_clicks'),
    State('strike-yaxis-column', 'value'))
def update_map(n_clicks, strike_yaxis_column_name):
    clicks = n_clicks

    dff = strikes[strikes['country'].isin(strike_yaxis_column_name)]

    heat_layer = pdk.Layer(
        "heatmapLayer",
        data=dff.query('type_of_strike == "Drone Strike"'),
        get_position=["longitude", "latitude"],
        aggregation="'SUM'",
        # color_range=COLOR_BREWER_BLUE_SCALE,
        threshold=1,
        get_weight="fatalities",
    )
    new_view_state = pdk.data_utils.compute_view(
        points=dff.query('type_of_strike == "Drone Strike"')[["longitude", "latitude"]], view_proportion=1)

    heat_r = pdk.Deck(layers=heat_layer, initial_view_state=new_view_state,
                      api_keys={'mapbox': mapToken}, map_provider='mapbox', tooltip=True)

    return heat_r.to_json()


if __name__ == '__main__':
    app.run_server(debug=True)

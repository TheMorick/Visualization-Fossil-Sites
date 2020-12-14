import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from copy import copy
import numpy as np

# Import and clean dataframe
fs = pd.read_csv('./fossil_sites.csv', escapechar='\\')

    # Some entries in the table have both a Site and a Group. Save that information in the Site column.
for i, row in fs.iterrows():
    if (type(fs.at[i,"Site"]) == str and type(fs.at[i,"Group, Formation, or Unit"]) == str):
        fs.at[i,"Site"] = fs.at[i,"Site"] + ", " + fs.at[i, "Group, Formation, or Unit"]
        # Some entries have NaN in the Noteworthiness and Country columns. Plotly does not like that. I fix.
    if type(fs.at[i,"Noteworthiness"]) == float: # NaN are stored as floats
        fs.at[i, "Noteworthiness"] = ""
    if type(fs.at[i,"Country"]) == float: # Sites in Antarctica don't have a country listed. More NaN's
        fs.at[i, "Country"] = ""

    # Where no Site name is given, substitute for a Group, Formation, or Unit name.
fs["Site"] = np.where(fs["Site"].isna(), fs["Group, Formation, or Unit"], fs["Site"]).astype("str")

    # With the information from Group, Formation, or Unit saved, we can safely delete it.
fs = fs.drop("Group, Formation, or Unit", axis=1)

# Set up helpful tools
timeline = {0: "Precambrian",
1: "Cambrian",
2: "Ordovician",
3: "Silurian",
4: "Devonian",
5: "Carboniferous",
6: "Permian",
7: "Triassic",
8: "Jurassic",
9: "Cretaceous",
10: "Paleocene",
11: "Eocene",
12: "Oligocene",
13: "Miocene",
14: "Pliocene",
15: "Pleistocene",
16: "Holocene"}

key_list = list(timeline.keys())
val_list = list(timeline.values())

# Utility functions for translating the Age column of the CSV into appropriate numbers.
def age_converter(age_text):
    ages = age_text.split()
    if len(ages) == 1:
        return [key_list[val_list.index(ages[0])]]
    else:
        return [key_list[val_list.index(ages[0])], key_list[val_list.index(ages[2])]]

def get_age_range(age_range_string):
    ages = age_converter(age_range_string)
    if len(ages) > 1:
        return [timeline[i] for i in range(ages[0],ages[1]+1)]
    return [timeline[ages[0]]]

def is_age_overlap(entry_age, age_restrict_list):
    age_range = get_age_range(entry_age)
    selected_range = [entry[1] for entry in age_restrict_list]
    for age in age_range:
        if age in selected_range:
            return True
    return False

def is_noteworthiness_overlap(entry_note, note_restrict_list):
    for note in note_restrict_list:
        if note.lower() in entry_note.lower():
            return True
    return False

def is_searched_for(entry, restrict_list):
    # Check if entry's age is within searched boundaries
    age_restrict_list = [i for i in restrict_list if i[0] == "Age"]
    if (len(age_restrict_list) > 0) and (not is_age_overlap(entry["Age"], age_restrict_list)):
        return False
    # Check if entry's country is searched for
    country_restrict_list = [i[1] for i in restrict_list if i[0] == "Country"]
    if (len(country_restrict_list) > 0) and (not (any_true([search.lower() in str(entry["Country"].lower()) for search in country_restrict_list]))):
        return False
    # Check if entry's noteworthiness is searched for
    note_restrict_list = [i[1] for i in restrict_list if i[0] == "Noteworthiness"]
    if (len(note_restrict_list) > 0) and (not is_noteworthiness_overlap(entry["Noteworthiness"], note_restrict_list)):
        return False
    # TODO: Check if entry's site name is searched for
    site_restrict_list = [i[1] for i in restrict_list if i[0] == "Site"]
    if (len(site_restrict_list) > 0) and (not (any_true([search.lower() in str(entry["Site"].lower()) for search in site_restrict_list]))):
        return False
    return True

# Stupid little helper function
def any_true(list_of_bools):
    for b in list_of_bools:
        if b:
            return True
    return False

# Function for creating the actucal application layout.
def create_figure(dataframe, restrict_list=None, point_colour_dict=None, label_colour_dict=None, map_style=None):
    return_data = copy(dataframe)
    return_data["Show"] = True
    # Find selected points via restrict_list
    if restrict_list:
        for i, row in return_data.iterrows():
            if not is_searched_for(row, restrict_list):
                return_data.at[i,"Show"] = False
        return_data = return_data[return_data["Show"] == True]
    # Set colour options
    if point_colour_dict:
        point_colour = point_colour_dict["hex"]
    else:
        point_colour = "#FF00FF" # A nice, calming fuchsia
    if label_colour_dict:
        label_colour = label_colour_dict["hex"]
    else:
        label_colour = "#FF00FF" # A second, equally nice fuchsia
    # If no points can be made, show empty map
    if len(return_data) == 0:
        fig = go.Figure(go.Scattermapbox(
            lon = return_data["Longitude"],
            lat = return_data["Latitude"],
        ))
    # Construct scatter_mapbox object displaying all selected point
    else:
        fig = px.scatter_mapbox(
            return_data,
            lat = "Latitude",
            lon = "Longitude",
            zoom = 1,
            hover_name = "Site",
            hover_data = ["Country", "Continent", "Age", "Noteworthiness"],
            color_discrete_sequence = [point_colour]
        )
    fig.layout = {
        'uirevision': True
    }
    fig.update_layout(
        mapbox_style = map_style,
        margin = {"r": 0, "t": 0, "l": 0, "b": 0},
        hoverlabel={
            "bgcolor":label_colour
        },
        height=600,
    )
    return fig


# Run Dash application
app = dash.Dash()

# Specify app layout
app.layout = html.Div([
    # Title
    html.H1(children='Fossil Sites Visualization'),
    # Map of fossil sites
    dcc.Graph(
        id = 'map-graph',
        figure = create_figure(fs, map_style='stamen-terrain')
    ),
    dcc.Tabs(
        id='tabs',
        value='search-criteria',
        children=[
            dcc.Tab(label='Search Criteria', value='search-criteria'),
            dcc.Tab(label='Display Options', value='colour-options')
        ]
    ),
    html.Div(id='tabs-content'),
    html.Div(
        id="search-criteria-div",
        style= {"display":"block"},
        children=[
            # Slider for selection of era range
            dcc.RangeSlider(
                id = 'time-rangeslider',
                min = 0,
                max = 16,
                marks = {i: timeline[i] for i in range(0,17)},
                value = [0,16],
                updatemode = 'drag',
            ),
                # Search boxes
            # Search box for country
            html.H4("Search for individual countries:"),
            dcc.Input(
                id="country_input",
                placeholder="Enter a country name...",
                type="text",
                value=''
            ),
            # Search box for noteworthiness
            html.H4("Search for specific finds:"),
            dcc.Input(
                id="note_input",
                placeholder="Enter a type of find...",
                type="text",
                value=''
            ),
            # Search box for site name
            html.H4("Search for names of sites or formations:"),
            dcc.Input(
                id="site_input",
                placeholder="Enter a site name...",
                type="text",
                value='',
            ),
            html.Div(
                html.H5("(Tip: When searching for multiple terms of the same kind (like countries), separate them by a comma and a space, like so: 'Denmark, USA, Brazil'.)"),
            ),
        ]),
    html.Div(
        id="display-options-div",
        style={"display":"none"},
        children=[
            html.Div([
                html.Div([
                    html.H4("Map Choices"),
                    dcc.RadioItems(
                        id="display-map-radio",
                        options=[
                            {'label':'Stamen Terrain','value':'stamen-terrain'},
                            {'label':'Stamen Toner','value':'stamen-toner'},
                            {'label':'Open Street Map','value':'open-street-map'},
                            {'label':'Carto Positron','value':'carto-positron'},
                            {'label':'Carto Darkmatter','value':'carto-darkmatter'}
                        ],
                        value='stamen-terrain',
                        labelStyle={"display":"block"}
                    ),
                    ],
                    style={"float":"left", "margin":"20px"}
                ),
                html.Div([
                    html.H4("Colour Choices"),
                    html.Div([
                        daq.ColorPicker(
                            id="point-colour-picker",
                            label="Point Colour",
                            value={"hex":'#FF00FF'}
                        ),
                        dcc.Checklist(
                            id="colour-toggle-checklist",
                            options=[
                                {'label': 'Choose point and label colours seperately', 'value':'yes'}
                            ],
                            value=[]
                        )],
                        style={"float":"left", "margin":"10px"}
                    ),
                    html.Div([
                        daq.ColorPicker(
                            id="label-colour-picker",
                            label="Label Colour",
                            value={"hex":'#FF00FF'}
                        )],
                        id="label-colour-picker-div",
                        style={"float":"left", "margin":"10px", "display":"none"}
                    )
                    ],
                    style={"float":"left", "margin":"20px"}
                )
                ]
            ),
        ]
    ),
])


@app.callback(
    Output('map-graph', 'figure'),
    [Input('time-rangeslider', 'value')],
    [Input('country_input', 'value')],
    [Input('note_input', 'value')],
    [Input('site_input', 'value')],
    [Input('point-colour-picker', 'value')],
    [Input('label-colour-picker', 'value')],
    [Input('colour-toggle-checklist', 'value')],
    [Input('display-map-radio', 'value')]
)
def display_map(era_range, country_input, note_input, site_input, point_colour_dict, label_colour_dict, colour_toggle_value, display_map_value):
    super_list = []
    if era_range != [0,16]:
        era_restrict_list = [("Age",timeline[i]) for i in range(era_range[0],era_range[1]+1)]
        super_list = super_list + era_restrict_list
    if country_input != "":
        if country_input[-1] == ',':
            country_input = country_input[:-1]
        country_inputs = country_input.split(", ")
        country_restrict_list = [("Country",country) for country in country_inputs]
        super_list = super_list + country_restrict_list
    if note_input != "":
        if note_input[-1] == ',':
            note_input = note_input[:-1]
        note_inputs = note_input.split(", ")
        noteworthiness_restrict_list = [("Noteworthiness",note) for note in note_inputs]
        super_list = super_list + noteworthiness_restrict_list
    if site_input != "":
        if site_input[-1] == ',':
            site_input = site_input[:-1]
        site_inputs = site_input.split(", ")
        site_restrict_list = [("Site",site) for site in site_inputs]
        super_list = super_list + site_restrict_list
    if colour_toggle_value != ["yes"]:
        label_colour_dict = point_colour_dict
    return create_figure(fs, super_list, point_colour_dict, label_colour_dict, display_map_value)

@app.callback(Output('search-criteria-div','style'),Input('tabs','value'))
def toggle_search_criteria(tab):
    if tab == 'search-criteria':
        return {"display":"block"}
    else:
        return {"display":"none"}

@app.callback(Output('display-options-div','style'),Input('tabs','value'))
def toggle_colour_options(tab):
    if tab == 'colour-options':
        return {"display":"block"}
    else:
        return {"display":"none"}

@app.callback(Output('label-colour-picker-div','style'),Input('colour-toggle-checklist','value'))
def toggle_colour_split(value):
    if value == ["yes"]:
        return {"float":"left", "margin":"10px", "display":"block"}
    else:
        return {"float":"left", "margin":"10px", "display":"none"}

if __name__ == '__main__':
    app.run_server()
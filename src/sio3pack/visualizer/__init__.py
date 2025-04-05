import base64

from sio3pack.visualizer import cytoscope

try:
    import dash
    import dash_cytoscape as cyto
    from dash import Input, Output, State, dcc, html
except ImportError:
    raise ImportError("Please install the 'dash' and 'dash-cytoscape' packages to use the visualizer.")

import json
import os
import sys


def main():
    app = dash.Dash(__name__)
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [],
                        style={"flex": "3", "height": "100vh"},
                        id="graph-div",
                    ),
                    html.Div(
                        [
                            html.Pre(
                                id="node-data",
                                style={
                                    "padding": "10px",
                                    "whiteSpace": "pre",
                                    "overflow": "auto",
                                    "maxHeight": "95vh",
                                    "maxWidth": "100%",
                                },
                            )
                        ],
                        style={"flex": "1", "height": "100vh", "backgroundColor": "#f7f7f7"},
                    ),
                ],
                id="graph",
                style={"display": "flex", "flexDirection": "row", "height": "100vh"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H1("SIO3Worker Visualizer"),
                            html.P(
                                "This is a visualizer for SIO3Worker's graph representation. <br>"
                                "Paste a JSON representation of the workflow in the text area below or upload a file."
                            ),
                        ],
                        style={"padding": "10px", "backgroundColor": "#f7f7f7"},
                    ),
                    html.Div(
                        [
                            dcc.Textarea(id="graph-input", placeholder="JSON description of the workflow"),
                            dcc.Upload(
                                id="graph-file",
                                children=html.Button("Upload File"),
                                multiple=False,
                            ),
                            html.Button("Load", id="load-button", n_clicks=0),
                        ]
                    ),
                ],
                id="input-container",
            ),
        ]
    )

    @app.callback(
        [
            Output("graph", "style"),
            Output("graph-div", "children"),
            Output("input-container", "style"),
        ],
        Input("load-button", "n_clicks"),
        [
            State("graph-input", "value"),
            State("graph-file", "contents"),
        ],
    )
    def show_graph(n_clicks, value, contents):
        if n_clicks > 0:
            if not value and not contents:
                return {"display": "flex"}, [], {"display": "block"}
            if value:
                file_content = value
            else:
                try:
                    content_type, content_string = contents.split(",")
                    file_content = base64.b64decode(content_string).decode("utf-8")
                except Exception as e:
                    print(e)
                    return {"display": "flex"}, [], {"display": "block"}
            graph = json.loads(file_content)
            elements = cytoscope.get_elements(graph)
            instance = cyto.Cytoscape(
                id="cytoscape",
                layout={"name": "breadthfirst", "directed": True},
                style={"width": "100%", "height": "100vh"},
                elements=elements,
                stylesheet=[
                    {
                        "selector": "node",
                        "style": {
                            "label": "data(label)",
                            "text-valign": "center",
                            "text-margin-y": "-20px",
                        },
                    },
                    {
                        "selector": "edge",
                        "style": {
                            "curve-style": "bezier",  # Makes edges curved for better readability
                            "target-arrow-shape": "triangle",  # Adds an arrowhead to indicate direction
                            "arrow-scale": 1.5,  # Makes the arrow larger
                            "line-color": "#0074D9",  # Edge color
                            "target-arrow-color": "#0074D9",  # Arrow color
                            "width": 2,  # Line thickness
                            "content": "data(label)",  # Show edge label on hover
                            "font-size": "12px",
                            "color": "#ff4136",
                            "text-background-opacity": 1,
                            "text-background-color": "white",
                            "text-background-shape": "roundrectangle",
                            "text-border-opacity": 1,
                            "text-border-width": 1,
                            "text-border-color": "#ff4136",
                        },
                    },
                    {
                        "selector": ".register",
                        "style": {
                            "shape": "rectangle",
                        },
                    },
                    {
                        "selector": ".script",
                        "style": {
                            "shape": "roundrectangle",
                        },
                    },
                    {
                        "selector": ".execution",
                        "style": {
                            "shape": "ellipse",
                        },
                    },
                    {
                        "selector": ".reactive",
                        "style": {
                            "background-color": "#ff851b",
                        },
                    },
                    {
                        "selector": ".exclusive",
                        "style": {
                            "background-color": "#ff4136",
                        },
                    },
                    {
                        "selector": "#input_storage",
                        "style": {
                            "shape": "rectangle",
                            "background-color": "#2ECC40",
                        },
                    },
                    {
                        "selector": "#output_storage",
                        "style": {
                            "shape": "rectangle",
                            "background-color": "#FF851B",
                        },
                    },
                ],
            )
            return (
                {"display": "flex", "flex-direction": "row", "height": "100vh"},
                instance,
                {"display": "none"},
            )
        return (
            {"display": "none"},
            None,
            {"display": "block"},
        )

    @app.callback(Output("node-data", "children"), Input("cytoscape", "tapNodeData"))
    def display_task_info(data):
        if data is None:
            return "Click on a node to see its info."
        if isinstance(data["info"], dict):
            return json.dumps(data["info"], indent=4)
        return data["info"]

    app.run()

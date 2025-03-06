from django.core.files.locks import kernel32
from django.shortcuts import render

try:
    import dash
    import dash_cytoscape as cyto
    from dash import html, Output, Input
except ImportError:
    raise ImportError("Please install the 'dash' and 'dash-cytoscape' packages to use the visualizer.")

import os
import sys
import json


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m sio3pack.visualizer <graph file>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not file_path.endswith(".json"):
        print("The file must be a JSON file.")
        sys.exit(1)
    if not os.path.isfile(file_path):
        print("The file does not exist.")
        sys.exit(1)

    graph = json.load(open(file_path))
    elements = []
    ins = {}
    rendered_registers = set()

    # Create nodes for observable registers.
    for register in range(graph["observable_registers"]):
        elements.append({
            "data": {
                "id": f"obs_register_{register}",
                "label": f"Observable register {register}",
                "info": "This is an observable register. It's an output of a workflow."
            },
            "classes": "register"
        })
        ins[register] = [f"obs_register_{register}"]
        rendered_registers.add(register)


    script_i = 0
    execution_i = 0
    # First pass to create nodes and mark input registers.
    for task in graph["tasks"]:
        if task["type"] == "script":
            id = f"script_{script_i}"
            elements.append({
                "data": {
                    "id": id,
                    "label": task.get("name", f"Script {script_i}"),
                    "info": task
                },
                "classes": "script"
            })
            if task["reactive"]:
                elements[-1]["classes"] += " reactive"
            script_i += 1
            for register in task["input_registers"]:
                if register not in ins:
                    ins[register] = []
                ins[register].append(id)
        elif task["type"] == "execution":
            id = f"execution_{execution_i}"
            elements.append({
                "data": {
                    "id": id,
                    "label": task.get("name", f"Execution {execution_i}"),
                    "info": task
                },
                "classes": "execution"
            })
            if task["exclusive"]:
                elements[-1]["classes"] += " exclusive"

            # To delete, final spec is different
            if "input_register" in task:
                register = task["input_register"]
                if register not in ins:
                    ins[register] = []
                ins[register].append(id)
            execution_i += 1

    # Second pass to create edges.
    script_i = 0
    execution_i = 0
    for task in graph["tasks"]:
        if task["type"] == "script":
            registers = task["output_registers"]
        elif task["type"] == "execution":
            registers = [task["output_register"]]
        else:
            raise

        for register in registers:
            if register not in ins:
                elements.append({
                    "data": {
                        "id": f"register_{register}",
                        "label": f"Register {register}",
                        "info": f"This is a register. It's an intermediate value in a workflow."
                    },
                    "classes": "register"
                })
                ins[register] = [f"register_{register}"]
                rendered_registers.add(register)
            for id in ins[register]:
                if task["type"] == "script":
                    elements.append({
                        "data": {
                            "source": f"script_{script_i}",
                            "target": id,
                        }
                    })
                elif task["type"] == "execution":
                    elements.append({
                        "data": {
                            "source": f"execution_{execution_i}",
                            "target": id,
                        }
                    })
                if register not in rendered_registers:
                    elements[-1]["data"]["label"] = f"via register {register}"

        if task["type"] == "script":
            script_i += 1
        elif task["type"] == "execution":
            execution_i += 1

    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.Div([
            cyto.Cytoscape(
                id='cytoscape',
                layout={"name": "breadthfirst", "directed": True},
                style={'width': '100%', 'height': '100vh'},
                elements=elements,
                stylesheet=[
                    {"selector": "node", "style": {
                        "label": "data(label)",
                        "text-valign": "center",
                        "text-margin-y": "-20px",
                    }},
                    {"selector": "edge", "style": {
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
                    }},
                    {"selector": ".register", "style": {
                        "shape": "rectangle",
                    }},
                    {"selector": ".script", "style": {
                       "shape": "roundrectangle",
                    }},
                    {"selector": ".execution", "style": {
                        "shape": "ellipse",
                    }},
                    {"selector": ".reactive", "style": {
                        "background-color": "#ff851b",
                    }},
                    {"selector": ".exclusive", "style": {
                        "background-color": "#ff4136",
                    }},
                ],
            ),
        ], style={"flex": "3", "height": "100vh"}),

        html.Div([
            html.Pre(id='node-data', style={
                "padding": "10px",
                "white-space": "pre",
                "overflow": "auto",
                "max-height": "95vh",
                "max-width": "100%"
            })
        ], style={"flex": "1", "height": "100vh", "background-color": "#f7f7f7"})
    ], style={"display": "flex", "flex-direction": "row", "height": "100vh"})

    @app.callback(
        Output('node-data', 'children'),
        Input('cytoscape', 'tapNodeData')
    )
    def display_task_info(data):
        if data is None:
            return "Click on a node to see its info."
        if isinstance(data["info"], dict):
            return json.dumps(data["info"], indent=4)
        return data["info"]

    app.run_server(debug=True)

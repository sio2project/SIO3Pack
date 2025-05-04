import os


def get_elements(graph):
    elements = []
    ins = {}
    ins_objects = {}
    rendered_registers = set()
    observable_objects = graph["observable_objects"]
    external_objects = graph["external_objects"]

    # Create node for input object storage and output object storage
    if len(external_objects) > 0:
        elements.append(
            {
                "data": {
                    "id": "input_storage",
                    "label": "Input object storage",
                    "info": "This is the object storage.\nEdges from this node are input object\n(external_objects) for the workflow.",
                }
            }
        )
    if len(observable_objects) > 0:
        elements.append(
            {
                "data": {
                    "id": "output_storage",
                    "label": "Output object storage",
                    "info": "This is the object storage.\n  Edges to this node are output object\n(observable_objects) for the workflow.",
                }
            }
        )

    # Mark observable objects as inputs for output object storage
    for object in observable_objects:
        if object not in ins_objects:
            ins_objects[object] = set()
        ins_objects[object].add("output_storage")

    # Create nodes for observable registers.
    for register in range(graph["observable_registers"]):
        elements.append(
            {
                "data": {
                    "id": f"obs_register_{register}",
                    "label": f"Observable register {register}",
                    "info": "This is an observable register. It's an output of a workflow.",
                },
                "classes": "register",
            }
        )
        ins[register] = [f"obs_register_{register}"]
        rendered_registers.add(register)

    script_i = 0
    execution_i = 0
    # First pass to create nodes and mark input registers.
    for task in graph["tasks"]:
        if task["type"] == "script":
            id = f"script_{script_i}"
            elements.append(
                {"data": {"id": id, "label": task.get("name", f"Script {script_i}"), "info": task}, "classes": "script"}
            )
            if task["reactive"]:
                elements[-1]["classes"] += " reactive"
            script_i += 1
            for register in task["input_registers"]:
                if register not in ins:
                    ins[register] = []
                ins[register].append(id)

            # Handle objects
            for object in task.get("objects", []):
                if object not in ins_objects:
                    ins_objects[object] = set()
                ins_objects[object].add(id)
        elif task["type"] == "execution":
            id = f"execution_{execution_i}"
            elements.append(
                {
                    "data": {"id": id, "label": task.get("name", f"Execution {execution_i}"), "info": task},
                    "classes": "execution",
                }
            )
            if task["exclusive"]:
                elements[-1]["classes"] += " exclusive"

            # Handle objects in descriptors of processes for the task
            for process in task["processes"]:
                for _, stream in process["descriptors"].items():
                    if stream["type"] == "object_read":
                        object = stream["handle"]
                        if object not in ins_objects:
                            ins_objects[object] = set()
                        ins_objects[object].add(id)

            # Handle objects in filesystems
            for filesystem in task["filesystems"]:
                if filesystem["type"] == "object":
                    object = filesystem["handle"]
                    if object not in ins_objects:
                        ins_objects[object] = set()
                    ins_objects[object].add(id)
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

        # Create edges from input registers to the task
        for register in registers:
            if register not in ins:
                elements.append(
                    {
                        "data": {
                            "id": f"register_{register}",
                            "label": f"Register {register}",
                            "info": f"This is a register. It's an intermediate value in a workflow.",
                        },
                        "classes": "register",
                    }
                )
                ins[register] = [f"register_{register}"]
                rendered_registers.add(register)
            for id in ins[register]:
                if task["type"] == "script":
                    elements.append(
                        {
                            "data": {
                                "source": f"script_{script_i}",
                                "target": id,
                            }
                        }
                    )
                elif task["type"] == "execution":
                    elements.append(
                        {
                            "data": {
                                "source": f"execution_{execution_i}",
                                "target": id,
                            }
                        }
                    )
                if register not in rendered_registers:
                    elements[-1]["data"]["label"] = f"via register {register}"

        # Create edges for objects
        if task["type"] == "script":
            # Script tasks cant create objects
            pass
        elif task["type"] == "execution":
            # Execution tasks can only create objects via descriptors
            for process in task["processes"]:
                for fd, stream in process["descriptors"].items():
                    if stream["type"] == "object_write":
                        object = stream["handle"]
                        for id in ins_objects.get(object, []):
                            elements.append(
                                {
                                    "data": {
                                        "source": f"execution_{execution_i}",
                                        "target": id,
                                        "label": f"via object {os.path.basename(object)} from fd {fd}",
                                    }
                                }
                            )

        if task["type"] == "script":
            script_i += 1
        elif task["type"] == "execution":
            execution_i += 1

    # Create edges from input object storage to the task
    for ext_object in external_objects:
        for id in ins_objects.get(ext_object, []):
            elements.append(
                {
                    "data": {
                        "source": "input_storage",
                        "target": id,
                        "label": f"via object {ext_object}",
                    }
                }
            )

    return elements

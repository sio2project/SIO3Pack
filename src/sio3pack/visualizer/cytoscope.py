def get_elements(graph):
    elements = []
    ins = {}
    rendered_registers = set()

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

        if task["type"] == "script":
            script_i += 1
        elif task["type"] == "execution":
            execution_i += 1

    return elements

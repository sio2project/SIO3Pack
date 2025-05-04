class Object:
    """
    A class to represent an object in a workflow.
    A object is a file, stored either locally or remotely.

    :param str handle: The handle of the object.
    """

    def __init__(self, handle: str):
        """
        Create a new object.

        :param handle: The handle of the object.
        """
        self.handle = handle

    def __str__(self):
        return f"<Object {self.handle}>"

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the object with the given replacements.

        :param replacements: The replacements to make.
        """
        for key, value in replacements.items():
            if key in self.handle:
                self.handle = self.handle.replace(key, value)


class ObjectsManager:
    def __init__(self):
        self.objects = {}

    def create_object(self, handle: str) -> Object:
        """
        Create and return a new object.
        :param handle: The handle of the object.
        :return: The created object.
        """
        obj = Object(handle)
        self.objects[handle] = obj
        return obj

    def add_object(self, obj: Object):
        """
        Add an object to the manager.
        :param obj: The object to add.
        """
        self.objects[obj.handle] = obj

    def get_object(self, handle: str) -> Object:
        """
        Get an object by its handle.
        :param handle: The handle of the object.
        """
        return self.objects[handle]

    def get_or_create_object(self, handle: str) -> Object:
        """
        Get an object by its handle, creating it if it does not exist.
        :param handle: The handle of the object.
        """
        if handle not in self.objects:
            return self.create_object(handle)
        return self.get_object(handle)


class ObjectList:
    """
    A class to represent a list of objects in a workflow.
    """

    def __init__(self):
        self.objects = []

    def append(self, obj: Object):
        """
        Append an object to the list.

        :param Object obj: The object to append.
        """
        self.objects.append(obj)

    def extend(self, objects: list[Object]):
        """
        Extend the list with the given objects.

        :param list[Object] objects: The objects to extend the list with.
        """
        self.objects.extend(objects)

    def __getitem__(self, index: int) -> Object:
        """
        Get an object by its index.

        :param int index: The index of the object.
        :return: The object at the given index.
        """
        return self.objects[index]

    def __len__(self) -> int:
        """
        Get the length of the list.

        :return: The length of the list.
        """
        return len(self.objects)

    def __str__(self):
        """
        Get the string representation of the list.

        :return: The string representation of the list.
        """
        return f"<ObjectList {len(self.objects)} objects>"

    def union(self, other: "ObjectList"):
        """
        Union the list with another list of objects.

        :param ObjectList other: The other list to union with.
        """
        objects = {}
        for obj in self.objects:
            objects[obj.handle] = obj
        for obj in other.objects:
            if obj.handle not in objects:
                objects[obj.handle] = obj
        self.objects = list(objects.values())

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

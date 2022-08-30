from abc import abstractproperty


class AppMetaClass(type):

    @abstractproperty
    def ro_conn(self):
        """
        return Tortoise.get_connection("ro_conn")
        """

    @abstractproperty
    def rw_conn(self):
        """
        return Tortoise.get_connection("rw_conn")
        """

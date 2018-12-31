import mysql.connector


class DBConnection:
    """
    Database connection object

    Parameters
    ------------
    username : String
        The username for accessing the MySQL database
    password : String
        The password to the database
    database : String
        The name of the database to query

    Holds an SQL connection to a database, performs commands, and
    automatically maintains the connection
    """
    def __init__(self, username, password, database):
        self._username = username
        self._password = password
        self._database = database
        self.cnx = mysql.connector.connect(user=username,
                                           password=password,
                                           database=database)
        self.cursor = self.cnx.cursor(buffered=True)

    def commit(self):
        """ Commit the executed commands """
        self.cnx.commit()

    def close(self):
        """ Closes the connection to the database """
        self.cursor.close()
        self.cnx.close()

    def ensure_sql_connection(self):
        """ Ensures the database connection is still active and, if not, reconnects """
        if not self.cnx.is_connected():
            self.cnx = mysql.connector.connect(user=self._username,
                                               password=self._password, 
                                               database=self._database)
            self.cursor = self.cnx.cursor(buffered=True)

    def execute(self, command, data=None):
        """
        Execute an SQL query with the provided data

        Parameters
        ------------
        command : String
            A string containing the command to execute.
            Variables for data replacement should use the '%s' keyword
            (e.g. 'INSERT INTO Users VALUES (%s, %s)')
        data : (String/Int)
            A tuple containing the data values
        """
        if data is None:
            self.cursor.execute(command)
        else:
            self.cursor.execute(command, data)
        return self.cursor

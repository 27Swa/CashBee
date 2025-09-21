import psycopg2
from psycopg2.extras import RealDictCursor
from mappers import *     
class PostgresSQl: 
    """Make a singleton to use it when working with data"""
    _instance = None    
    def __new__(cls):           
        if cls._instance is None:
            cls._instance = super(PostgresSQl, cls).__new__(cls)
            cls._instance.conn = psycopg2.connect(
            host="localhost",
            database="cashbee",
            user="postgres",
            password="So@1234",
            # To return data from the db a dictionary so that it's better to 
            # get the data
            cursor_factory=RealDictCursor 
        )
        cls._instance.cursor = cls._instance.conn.cursor()
        return cls._instance
    
    def execute(self, query,mapper = None, values=None):
        if values:
            self.cursor.execute(query, values)
        else:
            self.cursor.execute(query)
        if not query.strip().upper().startswith("SELECT"):
            self.conn.commit()
            if not "RETURNING"in query.upper():        
                return None  
        try:          
            rows = self.cursor.fetchall()
            if mapper:
                return [
                   mapper.from_dict(row) for row in rows
                ]
            return rows if len(rows) > 1 else rows[0] if rows else None

        except psycopg2.ProgrammingError:
            return None

    def close(self):
        self.cursor.close()
        self.conn.close()
        PostgresSQl._instance = None
class QueriesdInfoHandling:
    @staticmethod
    def insert_handling(col,data,mapper):
        # Handle data format to be correct written in the data
        data = mapper.to_dict(data)
        col_ = "(" + ", ".join(col) + ")"
        placeholders = "("+", ".join(["%s"] * len(data))+")" 
        return col_,placeholders,data
    @staticmethod
    def update_handling(col):
        pattern = ",".join([f"{i} = %s" for i in col])
        return pattern  
class QueryHandling:
    """
        Handling queries so that when need anything from db
        it will me the query 
        columns is passed as lists or tuples
    """
    db = PostgresSQl()
    @staticmethod
    def add_data(table,col, data,mapper,pk =None):
        col,place_holders,data = QueriesdInfoHandling.insert_handling(col,data,mapper)       
        pk = "RETURNING "+pk if pk else ""
        query = f"INSERT INTO {table} {col} VALUES {place_holders} {pk}"
        result = QueryHandling.db.execute(query, values = data)
        return result
    @staticmethod
    def update_data(table,col,cond,data):
        pt = QueriesdInfoHandling.update_handling(col)
        query = f"UPDATE {table} SET {pt} WHERE {cond}"
        QueryHandling.db.execute(query, values = data)
    @staticmethod
    def retrieve_data(table,mapper,col ="",cond="",data = None):
        if not col:
            col = '*'
        elif isinstance(col, (list, tuple)):
            col = ", ".join(col)
        
        cond = f"WHERE {cond}" if cond else ""
        query = f"SELECT {col} FROM {table} {cond}"
        result = QueryHandling.db.execute(query, values=data)
        if result:
            if isinstance(result, list) and len(result) > 0:
                return [mapper.from_dict(dict(row)) for row in result]
            else:
                return mapper.from_dict(dict(result))
        return None
    
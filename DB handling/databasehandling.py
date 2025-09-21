import json
import os


class DatabaseHandler:
    """
        Handling data usage in the system (read, update, delete)
    """
    def __init__(self, file_path="cashbee_db.json"):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            self._initialize_db()

    def _initialize_db(self):
        empty_structure = {
            "users": [],
            "wallets": [],
            "family_wallets": [],
            "organizations": [],
            "transactions": [],
            "counters": {
                "transaction_id": 0,
                "wallet_id": 0,
                "family_wallet_id": 0
            }
        }
        self._write_data(empty_structure)

    def _read_data(self):
        """Reading data from json file"""
        with open(self.file_path, "r") as f:
            return json.load(f)

    def _write_data(self, data):
        """Writing data in json file"""
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4, default=str)

    def add_record(self, table, record, mapper):
        """To add a record in the data"""
        data = self._read_data()
        data[table].append(mapper.to_dict(record))
        self._write_data(data)

    def find_one(self, table, condition, mapper):
        """ To get specific record in the data"""
        data = self._read_data()
        for item in data[table]:
            if condition(item):
                return mapper.from_dict(item)
        return None

    def find_many(self, table, condition, mapper):
        """To get many records at the moment"""
        data = self._read_data()
        results = []
        for item in data[table]:
            if condition(item):
                results.append(mapper.from_dict(item))
        return results

    def update_record(self, table, condition, update_func):
        """To update a record """
        data = self._read_data()
        updated = False
        for item in data[table]:
            if condition(item):
                update_func(item)
                updated = True
        if updated:
            self._write_data(data)
        return updated

    def delete_record(self, table, condition):
        """To delete a record"""
        data = self._read_data()
        initial_length = len(data[table])
        data[table] = [item for item in data[table] if not condition(item)]
        if len(data[table]) != initial_length:
            self._write_data(data)
            return True
        return False
    
    def get_next_id(self, counter_name):
        """ To get the next id from the data"""
        data = self._read_data()
        if "counters" not in data:
            data["counters"] = {"transaction_id": 0, "wallet_id": 0, "family_wallet_id": 0}        
        data["counters"][counter_name] += 1
        next_id = data["counters"][counter_name]
        self._write_data(data)
        return next_id

class DatabaseHandlerSingleton: 
    """Make a singleton to use it when working with data"""
    _instance = None    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = DatabaseHandler()
        return cls._instance

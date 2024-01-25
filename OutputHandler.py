import data_models as dm

class OutputHandler:
    def __init__(self, data: str):
        self.data_sets = []
        self.data_cur = data
        self.encoder = dm.Encoder().encode

    def get_sets(self):
        return self.data_sets
    
    def get_cur(self):
        return self.data_cur
    
    def add(self, data):
        self.data_sets.append(data)
        self.data_cur = data
        
    def encode(self):
        return self.encoder({"data_sets": self.data_sets})
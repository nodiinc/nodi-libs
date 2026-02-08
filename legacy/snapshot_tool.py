from pickle import dump, load
from shutil import move
from os.path import exists

class Snapshot:
    """Pickle Snapshot"""
    
    def __init__(self, path):
        self.snapshot = path
        self.tempfile = f'{path}.tmp'
    
    def store_data(self, data):
        """Store data to snapshot"""
            
        # Create temporary file
        with open(self.tempfile, 'wb') as pickle_f:
            dump(data, pickle_f)
        
        # Once temporary file created, move to snapshot file
        move(self.tempfile, self.snapshot)
    
    def restore_data(self):
        """Restore data from snapshot"""
        
        try:

            # If snapshot file exists, restore data
            if exists(self.snapshot):
                
                # Restore data from snapshot file
                with open(self.snapshot, 'rb') as pickle_f:
                    data = load(pickle_f)
                return data
            
            # If snapshot file does not exist, do nothing
            else:
                return None
        
        except:
            return None
    
if __name__ == '__main__':
    from time import time
    ss_o = Snapshot('/root/this/snap/edge.pkl')
    t = time()
    for i in range(1000):
        recover_d = ss_o.restore_data()
    print(time() - t)
    
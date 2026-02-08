class QueueMaf:
    """Queue Moving Average Filter"""

    def __init__(self, size=1, decimal=6):
        self._size = max(size, 1)
        self.decimal = decimal
        self.queue = []
        self.mean = 0

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = max(value, 1)
        if len(self.queue) > self._size:
            self.queue = self.queue[-self._size:]

    def add_sample(self, sample):
        self.sample = sample
        self.queue.append(self.sample)
        if len(self.queue) > self._size:
            self.queue.pop(0)
        self.mean = round(sum(self.queue) / len(self.queue), self.decimal)
        
class TickMaf:
    """Tick Moving Average Filter"""

    def __init__(self, size=1, decimal=6):
        self.size = max(size, 1)
        self.decimal = decimal
        self.sum = 0
        self.count = 0
        self.mean = 0
    
    def add_sample(self, sample):
        self.sample = sample
        if self.count < self.size:
            self.sum = self.sum + self.sample
            self.count += 1
        else:
            self.sum = self.sum / self.size * (self.size - 1) + self.sample
        self.mean = round(self.sum / self.count, self.decimal)
         
if __name__ == '__main__':
    taf = TickMaf(10)
    while True:
        sample = input("add input: ")
        taf.add_sample(float(sample))
        print(taf.count, taf.sum, taf.mean)

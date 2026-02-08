import csv

class Csv:
    """csv Tool"""
    """
    File Opening Modes
    - r: Read (default)
    - w: Write
    - x: Exclusive creation (occur failure if already exists)
    - a: Append
    - b: Binary
    - t: Text
    - +: Update (open disk file for update)
    - U: Universial (not in use)
    """

    def __init__(self, path, encoding='utf-8', header=True, delimiter=',', newline=''):
        self.path = path
        self.encoding = encoding
        self.header = header
        self.delimiter = delimiter
        self.newline = newline

    def read_header(self):
        """Read header"""
        with open(file=self.path,
                  mode='r',
                  encoding=self.encoding,
                  newline=self.newline) as file:
            if self.header:
                reader_o = csv.reader(file, delimiter=self.delimiter)
                header_i = next(reader_o)
                return header_i
            else:
                return None

    def read_data(self):
        """Read data"""
        with open(file=self.path,
                  mode='r',
                  encoding=self.encoding,
                  newline=self.newline) as file:
            reader_o = csv.reader(file, delimiter=self.delimiter)
            data_ll = [read_i for read_i in reader_o]
            if self.header:
                return data_ll[1:]
            else:
                return data_ll

    def count_data(self):
        """Count data quantity"""
        with open(file=self.path,
                  mode='r',
                  encoding=self.encoding,
                  newline=self.newline) as file:
            if self.header:
                return len(file.readlines()) - 1
            else:
                return len(file.readlines())

    def write_one(self, data_l):
        """Write 1-dimension list"""
        with open(file=self.path,
                  mode='w',
                  encoding=self.encoding,
                  newline=self.newline) as file:
            writer_o = csv.writer(file, delimiter=self.delimiter)
            writer_o.writerow(data_l)

    def write_many(self, data_ll):
        """Write 2-dimension list"""
        with open(file=self.path,
                  mode='w',
                  encoding=self.encoding,
                  newline=self.newline) as file:
            writer_o = csv.writer(file, delimiter=self.delimiter)
            writer_o.writerows(data_ll)

    def append_one(self, data_l):
        """Append 1-dimension list"""
        with open(file=self.path,
                  mode='a',
                  encoding=self.encoding,
                  newline=self.newline) as file:
            writer_o = csv.writer(file, delimiter=self.delimiter)
            writer_o.writerow(data_l)

    def append_many(self, data_ll):
        """Append 2-dimension list"""
        with open(file=self.path,
                  mode='a',
                  encoding=self.encoding,
                  newline=self.newline) as file:
            writer_o = csv.writer(file, delimiter=self.delimiter)
            writer_o.writerows(data_ll)
            
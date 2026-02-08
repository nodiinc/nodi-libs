from datetime import datetime

class Logger:
    """Logger"""

    def __init__(self, path, name=None, encoding='UTF-8'):
        self.path = path
        self.name = name
        self.encoding = encoding
    
    def info(self, message, to_print=False):
        self.logging('INFO', message, to_print)
    
    def debug(self, message, to_print=False):
        self.logging('DEBUG', message, to_print)
    
    def warning(self, message, to_print=False):
        self.logging('WARNING', message, to_print)
    
    def error(self, message, to_print=False):
        self.logging('ERROR', message, to_print)
    
    def critical(self, message, to_print=False):
        self.logging('CRITICAL', message, to_print)
        
    def logging(self, level, message, to_print):

        # Get current time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S, %f')
        
        # Format message
        full_message = f'[{current_time}][{self.name}][{level}] {message}\n'

        # to_print on console
        if to_print:
            print(full_message)
        
        # Write to file
        file_path = datetime.now().strftime(self.path)
        with open(file=file_path,
                  mode='a',
                  encoding=self.encoding) as file:
            file.write(full_message)
import linecache
import tracemalloc

class MemoryTool:
    """Memory Measuring Tool"""

    def __init__(self, report_num=10, key_type='lineno'):
        self.report_num = report_num
        self.key_type = key_type
        
        # Start memory tracing
        tracemalloc.start()
    
    def take_snapshot(self):
        """Take memory snapshot in line"""
        
        # Take memory snapshot
        self.snapshot = tracemalloc.take_snapshot()
    
    def print_snapshot(self):
        """Print memory snapshot"""
        
        # Filter trace from snapshot
        self.trace = self.snapshot.filter_traces((
            tracemalloc.Filter(False, '<frozen importlib._bootstrap>'),
            tracemalloc.Filter(False, '<unknown>'),
        ))
        
        # Refine total items from trace
        total_items = self.trace.statistics(self.key_type)
        
        # Cut top N items
        top_items = total_items[:self.report_num]
        
        # Print top N items
        print(f'Top {self.report_num} items\n')
        for n, i in enumerate(top_items, 1):
            frame = i.traceback[0]
            item_file = frame.filename
            item_line = frame.lineno
            item_code = linecache.getline(item_file, item_line).strip()
            item_size = i.size / 1024
            print((f'#{n}: {item_size:.1f}KB\n'),
                  (f'  > File: {item_file}\n'),
                  (f'  > Line: {item_line}\n'),
                  (f'  > Code: {item_code}\n'))
        
        # Print rest items
        rest_items = total_items[self.report_num:]
        if rest_items:
            rest_num = len(rest_items)
            rest_size = sum(i.size for i in rest_items) / 1024
            print(f'Rest {rest_num} items: {rest_size:.1f}KB')
        
        # Print total summary
        total_num = len(total_items)
        total_size = sum(i.size for i in total_items) / 1024
        print(f'Total {total_num} items: {total_size:.1f}KB\n')
    
import inspect

def print_current_line_number():
    stack = inspect.stack()
    frame = stack[1]
    file_name = frame.filename
    line_number = frame.lineno
    print(f'File {file_name} / Line {line_number}')
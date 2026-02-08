import random
import time

def slow_random(current_value, min_value, max_value, step):
    current_value += random.uniform(-step, step)
    current_value = max(min(current_value, max_value), min_value)
    return round(current_value, 2)

value = 0
while True:
    value = slow_random(value, 0, 100, 1)
    print(value)
    time.sleep(0.1)
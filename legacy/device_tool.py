import time
import platform
import psutil
import subprocess
from threading import Thread
from pkg.exception_tool import try_pass

KB = 1024
MB = 1024 ** 2
GB = 1024 ** 3
TB = 1024 ** 4
MEASURE_DECIMAL = 3
PERCENT_DECIMAL = 1

class DeviceTool:
    """Device Monitoring Tool"""
    
    def __init__(self):
        self.get_cpu_result = None

    @try_pass
    def get_time_zone(self):
        DST_tm, Non_DST_tm = time.tzname
        return Non_DST_tm

    @try_pass
    def get_os_platform(self):
        result = platform.platform()
        return result

    @try_pass
    def get_os_type(self):
        result = platform.system()
        return result

    @try_pass
    def get_os_version(self):
        info = platform.freedesktop_os_release()
        result = info["VERSION"]
        return result

    @try_pass
    def get_kernel_version(self):
        result = platform.release()
        return result
    
    @try_pass
    def get_cpu_architecture(self):
        result = platform.machine()
        return result
    
    @try_pass
    def get_libc_version(self):
        info = platform.libc_ver()
        result = "-".join(info)
        return result
    
    @try_pass
    def get_python_version(self):
        result = platform.python_version()
        return result

    @try_pass
    def get_cpu_info(self):
        result = platform.processor()
        return result

    @try_pass
    def get_cpu_frequency_ghz(self):
        frequency = psutil.cpu_freq()
        result = round(frequency.max / KB, MEASURE_DECIMAL)
        return result

    @try_pass
    def get_cpu_core_quantity(self):
        result = psutil.cpu_count()
        return result

    @try_pass
    def get_cpu_usage_perc(self, interval=1):

        def _get_cpu_usage_perc(interval):
            percent = psutil.cpu_percent(interval=interval)
            self.get_cpu_result = percent
        
        thread = Thread(target = _get_cpu_usage_perc,
                     args = (interval, ),
                     daemon = True)
        thread.start()
        result = self.get_cpu_result
        return result
        # htop
        # mpstat | tail -1 | awk '{print 100-$NF}'

    @try_pass
    def get_memory_total_gb(self):
        memory = psutil.virtual_memory()
        result = round(memory.total / GB, MEASURE_DECIMAL)
        return result
        # free | grep Mem | awk '{print $2}'

    @try_pass
    def get_swap_total_gb(self):
        swap = psutil.swap_memory()
        result = round(swap.total / GB, MEASURE_DECIMAL)
        return result
        # free | grep Swap | awk '{print $2}'

    @try_pass
    def get_disk_total_gb(self):
        disk = psutil.disk_usage('/')
        result = round(disk.total / GB, MEASURE_DECIMAL)
        return result
        # df / -hP 2>/dev/null | grep -v ^Filesystem | awk '{sum += $2} END {print sum}'
    
    @try_pass
    def get_sensors_temperature(self):
        results = {}
        data = psutil.sensors_temperatures()
        for board, contents in data.items():
            results[board] = {}
            for entry in contents:
                if entry.label == '':
                    label = None
                else:
                    label = entry.label
                results[board][label] = {
                    'curr': entry.current,
                    'high': entry.high,
                    'crit': entry.critical
                }
        return results

    @try_pass
    def get_memory_usage_gb(self):
        memory = psutil.virtual_memory()
        result = round(memory.used / GB, MEASURE_DECIMAL)
        return result
        # free | grep Mem | awk '{print $3}'

    @try_pass
    def get_memory_usage_perc(self):
        memory = psutil.virtual_memory()
        result = round(memory.percent, PERCENT_DECIMAL)
        return result

    @try_pass
    def get_swap_usage_gb(self):
        swap = psutil.swap_memory()
        result = round(swap.used / GB, MEASURE_DECIMAL)
        return result
        # free | grep Swap | awk '{print $3}'

    @try_pass
    def get_swap_usage_perc(self):
        swap = psutil.swap_memory()
        result = round(swap.percent, PERCENT_DECIMAL)
        return result

    @try_pass
    def get_disk_usage_gb(self):
        disk = psutil.disk_usage('/')
        result = round(disk.used / GB, MEASURE_DECIMAL)
        return result
        # df / -hP 2>  | grep -v ^Filesystem | awk '{sum += $3} END {print sum}'

    @try_pass
    def get_disk_usage_perc(self):
        disk = psutil.disk_usage('/')
        result = round(disk.percent, PERCENT_DECIMAL)
        return result

    @try_pass
    def get_dir_size_gb(self, path):
        command = ['du', '-s', path]
        result = subprocess.run(command, stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8').strip()
        size_kb = output.split()[0]
        result = round(int(size_kb) / MB, MEASURE_DECIMAL)
        return result
from datetime import datetime
from dateutil.relativedelta import relativedelta
from re import match, findall
from typing import List, Union
from croniter import croniter

class TimeDiff:
    """Time Difference Tool"""
    
    def __init__(self,
                 delta_str: str='0-0-0 0:0:0.0',
                 base_time: datetime=None):
        self.set_base(base_time)
        self.delta_time = self._interpret_delta(delta_str)
    
    def set_base(self, base_time: datetime=None) -> None:
        """Set base time"""

        if base_time is None:
            self.base_time = datetime.now()
        else:
            self.base_time = base_time

    def get_next(self, number: int=1) -> List[datetime]:
        """Get next time after delta time"""

        results = []
        for _ in range(number):
            result = self.base_time + self.delta_time
            results.append(result)
            self.set_base(result)
        return results

    def get_prev(self, number: int=1) -> List[datetime]:
        """Get previous time before delta time"""

        results = []
        for _ in range(number):
            result = self.base_time - self.delta_time
            results.append(result)
            self.set_base(result)
        return results
    
    def _interpret_delta(self, delta_string: str) -> relativedelta:
        """Interpret delta expression"""
        
        # Check if delta string matches with pattern
        # pattern = r'^\d+-\d+-\d+ \d+:\d+:\d+\.\d+$'
        pattern = r'^\d+-\d+-\d+ \d+:\d+:\d+$'
        if not match(pattern, delta_string):
            raise TypeError('Unacceptable time format')
        
        # Extract numbers from delta string
        numbers = findall(r'\d+', delta_string)
        numbers = [int(num) for num in numbers]
        
        # Get time units from numbers
        years = numbers[0]
        months = numbers[1]
        days = numbers[2]
        hours = numbers[3]
        minutes = numbers[4]
        seconds = numbers[5]
        # microseconds = numbers[6]
        
        # Get delta time
        delta_time = relativedelta(years=years,
                                   months=months,
                                   days=days,
                                   hours=hours,
                                   minutes=minutes,
                                   seconds=seconds,
                                   microsecond=0)
        return delta_time

class TimeCron:
    """Cron Tool"""
    
    def __init__(self,
                 cron_expr: str='* * * * * *',
                 base_time: datetime=None,
                 time_format: Union[datetime, float]=datetime):
        self.cron_expr = cron_expr
        self.time_format = time_format
        self.set_base(base_time)
    
    def set_base(self, base_time: datetime=None) -> None:
        """Set base time"""

        if base_time is None:
            self.base_time = datetime.now()
        else:
            self.base_time = base_time

    def get_next(self, number: int=1) -> List[Union[datetime, float]]:
        """Get next cron schedule time"""

        results = []
        cron_o: croniter = self._interpret_cron(self.cron_expr,
                                                self.base_time,
                                                self.time_format)
        for _ in range(number):
            result = cron_o.get_next()
            results.append(result)
        return results

    def get_prev(self, number: int=1) -> List[Union[datetime, float]]:
        """Get previous cron schedule time"""

        results = []
        cron_o: croniter = self._interpret_cron(self.cron_expr,
                                                self.base_time,
                                                self.time_format)
        for _ in range(number):
            result = cron_o.get_prev()
            results.append(result)
        return results
        
    def _interpret_cron(self,
                        cron_expr: str,
                        base_time: datetime,
                        time_format: Union[datetime, float] ) -> croniter:
        """Interpret cron expression"""
        
        # Parse cron expression
        [self.month, self.date, self.weekday,
         self.hour, self.minute, self.second] = cron_expr.split(' ')
        
        # Process custom N symbol (= current time = start time)
        self.month = self.month.replace('N', str(self.base_time.month))
        self.date = self.date.replace('N', str(self.base_time.day))
        self.weekday = self.weekday.replace('N', str(self.base_time.weekday())) 
        self.hour = self.hour.replace('N', str(self.base_time.hour))
        self.minute = self.minute.replace('N', str(self.base_time.minute))
        self.second = self.second.replace('N', str(self.base_time.second))
        
        # Create Croniter expression
        croniter_expr = ' '.join([self.minute, self.hour, self.date,
                                  self.month, self.weekday, self.second])
        
        # Create croniter instance
        return croniter(expr_format=croniter_expr,
                        start_time=base_time,
                        ret_type=time_format)
        
if __name__ == '__main__':
    from time import sleep
    
    # t = TimeDiff('1-0-0 0:0:0')
    t = TimeCron('* * * 0 0 0')
    print(t.base_time)
    for i in t.get_next(10):
        print(i)


"""
* nodi cron: 5~6 fields
    +-----+-------+------------------+---------------+
    | no. | field | range            | symbol        |
    +-----+-------+------------------+---------------+
    | 1   | mth   | 1~12 | JAN~DEC   | * - , / N     |
    +-----+-------+------------------+---------------+
    | 2   | dat   | 1~31             | * - , / N L   |
    +-----+-------+------------------+---------------+
    | 3   | wk    | 0~6  | SUN~SAT   | * - , / N #   |
    +-----+-------+------------------+---------------+
    | 4   | hr    | 0~24             | * - , / N     |
    +-----+-------+------------------+---------------+
    | 5   | min   | 0~59             | * - , / N     |
    +-----+-------+------------------+---------------+
    | 6   | sec   | 0~59             | * - , / N     |
    +-----+-------+------------------+---------------+
    
* croniter cron: 5~6 fields
    +-----+-------+------------------+---------------+
    | no. | field | range            | symbol        |
    +-----+-------+------------------+---------------+
    | 1   | min   | 0~59             | * - , /       |
    +-----+-------+------------------+---------------+
    | 2   | hr    | 0~24             | * - , /       |
    +-----+-------+------------------+---------------+
    | 3   | dat   | 1~31             | * - , / L     |
    +-----+-------+------------------+---------------+
    | 4   | mth   | 1~12 | JAN~DEC   | * - , /       |
    +-----+-------+------------------+---------------+
    | 5   | wk    | 0~6  | SUN~SAT   | * - , / #     |
    +-----+-------+------------------+---------------+
    | 6   | sec   | 0~59             | * - , /       |
    +-----+-------+------------------+---------------+

* regular cron: 7 fields
    +-----+-------+------------------+---------------+
    | no. | field | range            | symbol        |
    +-----+-------+------------------+---------------+
    | 1   | sec   | 0~59             | * - , /       |
    +-----+-------+------------------+---------------+
    | 2   | mic   | 0~59             | * - , /       |
    +-----+-------+------------------+---------------+
    | 3   | hr    | 0~23             | * - , /       |
    +-----+-------+------------------+---------------+
    | 4   | dat   | 1~31             | * - , / ? L W |
    +-----+-------+------------------+---------------+
    | 5   | mth   | 1~21 | JAN~DEC   | * - , /       |
    +-----+-------+------------------+---------------+
    | 6   | dy    | 0~6  | SUN~SAT   | * - , / ? L # |
    +-----+-------+------------------+---------------+
    | 7   | yr    | None | 1970~2099 | * - , /       |
    +-----+-------+------------------+---------------+

* Symbols
    +--------+----------------+-------------+----------------------+
    | symbol | description    | example     | note                 |
    +--------+----------------+-------------+----------------------+
    | *      | all            |             |                      |
    +--------+----------------+-------------+----------------------+
    | -      | range          | MON-WED     |                      |
    +--------+----------------+-------------+----------------------+
    | ,      | list           | MON,TUE,WED |                      |
    +--------+----------------+-------------+----------------------+
    | /      | start/unit     | */5         | every 5min           |
    +--------+----------------+-------------+----------------------+
    | N      | now            |             |                      |
    +--------+----------------+-------------+----------------------+
    | ?      | none           |             |                      |
    +--------+----------------+-------------+----------------------+
    | L      | last           |             |                      |
    +--------+----------------+-------------+----------------------+
    | W      | coming_weekday |             | MON~FRI              |
    +--------+----------------+-------------+----------------------+
    | #      | day/week       | 3#2         | FRI of week2         |
    +--------+----------------+-------------+----------------------+
"""
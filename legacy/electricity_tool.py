from math import trunc


def calculate_float_energy(energy_float: float,
                           energy_int_raw: int,
                           power_float_raw: float,
                           meter_comm: bool = True,
                           update_cycle_sec: float = 1,
                           decimal: int = 6,
                           energy_is_signed: bool = False) -> float:
    """Calculate float energy from integer energy and float power"""
    
    # Create essential data 1
    energy_float_now = float(energy_float)
    
    # If meter communication is not ok, return now-float-energy as is
    meter_comm = True if meter_comm == 'True' or meter_comm == True or meter_comm == '1' else False
    if not meter_comm:
        return energy_float_now

    # Create essential data 2
    energy_float_now_trunc = trunc(energy_float_now)
    energy_int_raw = float(int(energy_int_raw))
    power_float_raw = float(power_float_raw)
    energy_float_new = round(energy_float_now + power_float_raw * update_cycle_sec / 3600, decimal)
    energy_float_added = energy_float_new - energy_int_raw

    # If energy is unsigned
    if not energy_is_signed:
        if energy_int_raw >= energy_float_now_trunc + 1:
            return energy_int_raw
        if energy_int_raw <= energy_float_now_trunc - 1:
            return energy_float_now
        if abs(energy_float_added) < 1 and energy_float_new > energy_float_now:
            return energy_float_new
    
    # If energy is signed
    else:
        if abs(energy_int_raw - energy_float_now_trunc) > 1 and abs(energy_float_added) >= 1:
            if abs(energy_float_now - energy_int_raw) >= 1:
                return energy_int_raw
            else:
                return energy_float_new
        if abs(energy_float_added) < 1:
            return energy_float_new
    
    # Else, return now-float-energy as is
    return energy_float_now


if __name__ == '__main__':
    energy_float = 0.0
    energy_int = 0
    power_float = 0.0
    energy_is_signed = False
    
    while True:
        meter_comm = input('meter_comm: ')
        energy_int = input('energy_int: ')
        power_float = input('power_float: ')
        energy_float = calculate_float_energy(energy_float, energy_int, power_float, meter_comm, energy_is_signed=energy_is_signed)
        print(f'energy_float: {energy_float}\n')
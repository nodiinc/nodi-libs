# Modbus Server

## Memory Area 0
* Explanation      : Discrete output coils
* R/W type of addr : rw
* Data address     : 00000~09999
* Data unit        : 1bit
* Relevant FC no.
```
FC01 : Read multiple
FC05 : Write single
FC15 : Write multiple
```

## Memory Area 1
* Explanation      : Discrete input coils
* R/W type of addr : ro
* Data address     : 10000~19999
* Data unit        : 1bit
* Relevant FC no.
```
FC02 : Read multiple
```

## Memory Area 3
* Explanation      : Input registers
* R/W type of addr : ro
* Data address     : 30000~39999
* Data unit        : 1word (2bytes)
* Relevant FC no.
```
FC04 : Read multiple
```

## Memory Area 4
* Explanation      : Holding registers
* R/W type of addr : rw
* Data address     : 40000~49999
* Data unit        : 1word (2bytes)
* Relevant FC no.
```
FC03 : Read multiple
FC06 : Write single
FC16 : Write multiple
```

# Modbus Client

## Function Code 01
* Explanation      : Read multiple read/writable discrete output coils
* R/W type of FC   : ro
* R/W type of addr : rw
* Data address     : 00000~09999
* Data unit        : 1bit
* Max block size   : 2000bits (250bytes)

## Function Code 02
* Explanation      : Read multiple read-only discrete input coils
* R/W type of FC   : ro
* R/W type of addr : ro
* Data address     : 10000~19999
* Data unit        : 1bit
* Max block size   : 2000bits (250bytes)

## Function Code 03
* Explanation      : Read multiple read/writable analog output holding registers
* R/W type of FC   : ro
* R/W type of addr : rw
* Data address     : 40000~49999
* Data unit        : 1word (2bytes)
* Max block size   : 125words (250bytes)

## Function Code 04
* Explanation      : Read multiple read-only analog input registers
* R/W type of FC   : ro
* R/W type of addr : ro
* Data address     : 30000~39999
* Data unit        : 1word (2bytes)
* Max block size   : 125words (250bytes)

## Function Code 05
* Explanation      : Write single read/writable discrete output coil
* R/W type of FC   : wo
* R/W type of addr : rw
* Data address     : 00000~09999
* Data unit        : 1bit
* Max block size   : 1bit

## Function Code 06
* Explanation      : Write single read/writable analog output holding register
* R/W type of FC   : wo
* R/W type of addr : rw
* Data address     : 40000~49999
* Data unit        : 1word (2bytes)
* Max block size   : 1word (2bytes)

## Function Code 15
* Explanation      : Write multiple read/writable discrete output coils
* R/W type of FC   : wo
* R/W type of addr : rw
* Data address     : 00000~09999
* Data unit        : 1bit
* Max block size   : 1bit

## Function Code 16
* Explanation      : Write multiple read/writable analog output holding registers
* R/W type of FC   : wo
* R/W type of addr : rw
* Data address     : 40000~49999
* Data unit        : 800bits (100bytes)
* Max block size   : 100word (200bytes)
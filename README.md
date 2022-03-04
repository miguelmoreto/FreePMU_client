# FreePMU Client

*This program is under development.*

The FreePMU client is multiplataform an open source program to test connection and read data from Phasor Measurement (PMU) Devices. It is developed to simplify the testing and data acquisition of FreePMU devices. This it is not needed to deploy a full Phasor Data Concentrator in order to be able to read data from FreePMU (and other PMUs as well[^1]).

This program is part of the FreePMU project.

## Characteristics

* Open source and multi-plataform (written in python)
* Can connect to multiple PMUs
* Easy plot real time data from multiple channels
* Export monitored data to CSV formats
* Compatible with [IEEE C37.118.2-2011](https://ieeexplore.ieee.org/document/6111222)
* Plot data from the stored data files ([pandas](https://pandas.pydata.org/) dataframes).

## Limitations

* Support only TCP connections.
* Parses only Configuration Frames 1 and 2 from  [IEEE C37.118.2-2011](https://ieeexplore.ieee.org/document/6111222) standard.
* Data from different PMUs in the real-time plot  is not guaranteed to be synchronized to each other. The data are just plotted as they arrived (in the export data file and offiline analysis the data is synchronized by the timestamp).
* Does not deals with analog and digital channels (only phasores).


- - -


![Federal University of Santa Catarina](./images/ufsc_logo.png?raw=true)

![Technological University of Parana](./images/utfpr_logo.png?raw=true)

[^1]: This was not tested yet.
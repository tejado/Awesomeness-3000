# Awesomeness-Portchecker-3000
Simple port/firewall tester in python. Should be compatible with python 2.x and 3.x without any additional packages. Really helpful to check large amounts of firewall rules in closed environments.

* Destinations will be provided in CSV format.
* IPv4 / IPv6
* TCP and an experimantal UDP support
* Python 2.x and 3.x
* ECONNREFUSED can be interpretet differently

## Examples
---
Create a file called ports.csv and put this in there:
```
10; Internet - google.net; www.google.net; 80; 443
```

Then go into your terminal and type:
```
python portchecker.py ports.csv
```
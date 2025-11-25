# IEEE GNSS-IR High School Physics Project

The hardware in this project was base on the work by Fagundes, M.A.R., Mendonça-Tinti, I., Iescheck, A.L. et al.
An open-source low-cost sensor for SNR-based GNSS reflectometry: design and long-term validation towards sea-level
altimetry. GPS Solut 25, 73 (2021). https://doi.org/10.1007/s10291-021-01087-1

## Overview
The goal of this project is to build a simple, effective, low-cost GNSS-IR system to monitor environmental changes.
This project is currently being piloted at some high schools in New Zealand. The project aims to give high school students
hands-on experience with GNSS-IR technology, it's application in real-world environments, how the physics behind GNSS-IR works
and how to analyze GNSS-IR data.

In 2025, we have:
- Had students learn from experts in the field through webinars and workshops
- Students developed and built a power system for the GNSS-IR hardware
- Learn how to select suitable locations for GNSS-IR data collection
- Students deploy hardware to collect GNSS-IR data
- Monitored snow depth changes at Snow Farm, Wānaka, New Zealand

## Quick Links
- [Hardware Build Tutorial](https://ajayacst.github.io/gnss-ir-docs/v1.1.0/build-tutorial-v1-1.html)
- [Parts List](https://ajayacst.github.io/gnss-ir-docs/v1.1.0/parts-list-v1-1.html)
- [Software Guide](https://ajayacst.github.io/gnss-ir-docs/v1.1.0/software-guide-v1-1-0.html)
- [PDF Version of Docs](https://github.com/AjayACST/gnss-ir-docs/releases/download/v1.1.0/pdfSourceV1.1.0.pdf)

## Hardware
We have a hardware build tutorial and parts list available through our documentation site: https://ajayacst.github.io/gnss-ir-docs/v1.1.0/build-tutorial-v1-1.html

## Running the Data Processing Software
The data parsing and processing software has been written in Python, translated from MATLAB code by Dr. Delwyn Moller.
The main files you will need are located in the `python` folder.

To get started you will need to install the required Python packages. You can do this using pip:

```bash
pip install -r requirements.txt
```

Data should be placed inthe `data` folder, then run the python script matlab_translate.py to process the data.
The data that should be processed is defined in the script at line 10:
```python
files_path = data_path.rglob("2505*.LOG")
```

Simply change the string "2505*.LOG" to match the files you want to process. In this instance it will process all files
starting with "2505" and ending with ".LOG".

For more detailed instructions on how to use the data processing software, please see the [](Software-Guide-V1.1.0.md).

## Contributing
We welcome contributions from anyone interested in GNSS-IR technology and its applications. If you would like to contribute,
please fork the repository and submit a pull request with your changes.
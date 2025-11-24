from pathlib import Path
from datetime import datetime

from python.process_gnss import GNSSProcessor
from readGPS import readGPS


if __name__ == "__main__":
    data_path = Path("../data")
    files_path = data_path.rglob("2505*.LOG") # change this pattern to match your files use *.LOG for all log files
    files_path = sorted(files_path, key=lambda x: x.name)

    gnss_processor = GNSSProcessor()

    for file in files_path:
        print("Parsing file:", file.name)
        gnss_data = readGPS(file, True)
        gnss_processor.process_gnss(gnss_data)


    choice = ""
    while choice != "3":
        print("Select option to graph:")
        print("0 - Plot Azimuths by Region for a Date")
        print("1 - Plot Retrieval Metrics for a Date")
        print("2 - Plot height over time")
        print("3 - Exit")

        choice = input("Enter choice: ")

        if choice == "0":
            date = input("Enter date in YYYY-MM-DD format: ")
            datetime_input = datetime.strptime(date, "%Y-%m-%d")
            gnss_processor.graph_azimuths(datetime_input)
        elif choice == "1":
            date = input("Enter date in YYYY-MM-DD format: ")
            datetime_input = datetime.strptime(date, "%Y-%m-%d")
            gnss_processor.graph_azimuths(datetime_input)
        elif choice == "2":
            gnss_processor.graph_height_time()
        elif choice == "3":
            exit(1)
        else:
            print("Invalid input")
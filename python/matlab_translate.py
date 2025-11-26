from pathlib import Path
from datetime import datetime

from python.process_gnss import GNSSProcessor
from readGPS import readGPS


if __name__ == "__main__":
    data_path = Path("../sample_data/farm")
    files_path = data_path.rglob("250520*.LOG") # change this pattern to match your files use *.LOG for all log files
    files_path = sorted(files_path, key=lambda x: x.name)
    print("The default azimuth range is 0-360 degrees.")
    print("If you wish to limit this azimuth range please provide this now in the format 'min max' (e.g., '90 270').")
    print("You can use multiple ranges, just press enter after the first range and provide the next range when prompted.")
    print("If you wish to use the default range, just press enter.")
    az_range_in = []
    while True:
        az_range_str = input("Enter azimuth range (or press enter to finish): ")
        if az_range_str == "":
            break
        try:
            az_min, az_max = map(float, az_range_str.split())
            if 0 <= az_min < az_max <= 360:
                az_range_in.append((az_min, az_max))
            else:
                print("Invalid range. Please ensure 0 <= min < max <= 360.")
        except ValueError:
            print("Invalid input. Please enter two numbers separated by a space.")

    if not az_range_in:
        az_range_in = [(0, 360)]
    print("Using azimuth ranges:", az_range_in)
    gnss_processor = GNSSProcessor(az_range_in)

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
            gnss_processor.graph_retrieval_metrics(datetime_input)
        elif choice == "2":
            gnss_processor.graph_height_time()
        elif choice == "3":
            exit(0)
        else:
            print("Invalid input")
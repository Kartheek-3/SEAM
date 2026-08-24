import csv

def print_csv_rows(file_path):
    try:
        with open(file_path, 'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                print(row)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")

print_csv_rows('data.csv')
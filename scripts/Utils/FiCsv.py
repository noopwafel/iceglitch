from csv import DictReader, DictWriter
import datetime

class FiCsvWriter():
    def __init__(self, file_path):
        self.file_path = file_path
        self.csv_writer = None
        self.last_insert_time = None

    def write(self, entry):
        if not self.csv_writer:
            self._first_write(entry)

        self._print_row(entry)
        self.csv_writer.writerow(entry)

    def _print_row(self, entry):
        if not self.last_insert_time:
            self.last_insert_time = datetime.datetime.now()

        print("Elapsed:", datetime.datetime.now() - self.last_insert_time, end=' ')
        for key, value in entry.items():
            if isinstance(value, float):
                print(key, '%.4G'%value, end=' ')
            else:
                print(key, value, end=' ')
        print('')
        self.last_insert_time = datetime.datetime.now()

    def _first_write(self, entry):
        self.csv_writer = DictWriter(open(self.file_path,'w'),fieldnames=entry.keys())
        self.csv_writer.writeheader()

class FiCsvReader():
    def __init__(self, file_path):
        self.csv_reader = DictReader(open(file_path,'r'))

    def read_all(self):
        return list(reader)



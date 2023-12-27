import os
import logging
import random

class NamesFileHandler:
    def __init__(self, logger=None, directory: str = None):
        self.logger = logger or logging
        self.directory = directory if directory is not None else input(
            "Enter directory path: ")
        self.names = []
        self.billing_value_per_name = 18

    def get_names(self):
        return self.names

    def get_billing_value_per_name(self, billing_value: int):
        return self.billing_value_per_name + (billing_value * 0.07)
    
    
    def get_names_billing_sub_set(self, name_count: int):
        names = self.get_names()
        first_name = names[0]
        subset = names[1:]
        random.shuffle(subset)
        subset = subset[:name_count - 1]
        return [first_name] + subset

    def get_names_and_write_to_file(self):
        names = []
        user_name = input("Please enter your name: ")
        if user_name:
            names.append(user_name)

        while True:
            name = input("Enter another name (or press Enter to finish): ")

            if name == "":
                break

            names.append(name)

        with open(os.path.join(self.directory, "names.txt"), "w") as file:
            for name in names:
                file.write(name + "\n")

        return names

    def read_existing_names(self):
        file_path = os.path.join(self.directory, "names.txt")
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                print("Contents of existing 'names.txt' file:")
                lines = []
                for line in file:
                    print(line.strip())
                    lines.append(line.strip())
                return lines
        return None

    def run(self):
        if os.path.exists(self.directory):
            existing_names = self.read_existing_names()
            if existing_names:
                print(f"Using the existing {os.path.join(self.directory, 'names.txt')}.")
            else:
                names = self.get_names_and_write_to_file()
                print(f"{names}\nhave been written to a new 'names.txt' file.")
            
            self.names = existing_names or names

if __name__ == "__main__":
    NamesFileHandler().run()

import os
import logging
import random

class UserData:
    def __init__(self, names: list = None, projects: list = None):
        self.names = names or []
        self.projects = projects or []
    
    def get(self, key: str):
        return getattr(self, key, None)
    
    def getAll(self):
        return self.__dict__
    
    def set(self, key: str, value: str):
        setattr(self, key, value)
        
    def setDataFromFile(self, file_path: str):
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                # get contents of file
                data = [[], []]
                i = 0
                for line in file:
                    line = line.strip()
                    if line == '######':
                        i+=1
                    else:
                        data[i].append(line)
                names, projects = data
        self.set("names", names)
        self.set("projects", projects)

class UserDataHandler:
    def __init__(self, logger=None, directory: str = None):
        self.logger = logger or logging
        self.directory = directory if directory is not None else input(
            "Enter directory path: ")
        self.data = UserData()
        self.billing_value_per_name = 18
        self.user_data_file = "user_data.txt"
        self.user_data_separator = "######"

    def get_names(self):
        return self.data.get("names")
    
    def get_projects(self):
        return self.data.get("projects")

    def get_billing_value_per_name(self, billing_value: int):
        return self.billing_value_per_name + (billing_value * 0.08)
    
    def get_names_billing_sub_set(self, name_count: int):
        names = self.get_names()
        first_name = names[0]
        subset = names[1:]
        random.shuffle(subset)
        subset = subset[:name_count - 1]
        return [first_name] + subset

    def get_topic(self, index: int = None):
        topics = self.get_projects()
        random.shuffle(topics)
        index = index if index is not None and index < len(topics) else random.randint(0, len(topics) - 1)
        return topics[index]

    def get_data_and_write_to_file(self):
        user_name = input("Please enter your name: ")
        if user_name:
            self.data.names.append(user_name)

        while True:
            name = input("Enter another name (or press Enter to finish): ")
            if name == "":
                break

            self.data.names.append(name)

        while True:
            project = input("Enter a project (or press Enter to finish): ")

            if project == "":
                break

            self.data.projects.append(project)
            
        with open(os.path.join(self.directory, self.user_data_file), "w") as file:
            names = "\n".join(self.data.names)
            projects = "\n".join(self.data.projects)
            file_contents = f"{names}\n{self.user_data_separator}\n{projects}"
            file.write(file_contents)

        return file_contents
    
    def read_existing_data(self):
        file_path = os.path.join(self.directory, self.user_data_file)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                print("Contents of existing 'user_data.txt' file:")
                lines = []
                for line in file:
                    data = line.strip()
                    if data == self.user_data_separator:
                        break
                    print(data)
                    lines.append(data)
                return lines
        return None

    def run(self):
        if os.path.exists(self.directory):
            existing_data = self.read_existing_data()
            if existing_data:
                print(f"Using the existing {os.path.join(self.directory, self.user_data_file)}.")
            else:
                data = self.get_data_and_write_to_file()
                print(f"{data}\nhave been written to a new {self.user_data_file} file.")
            
            self.data.setDataFromFile(os.path.join(self.directory, self.user_data_file))

if __name__ == "__main__":
    user_data = UserDataHandler(directory='/Users/loom23/Sites/python-receipts-manager/essen/IBT')
    user_data.run()
    subset = user_data.get_names_billing_sub_set(5)
    topic = user_data.get_topic()
    print(subset)
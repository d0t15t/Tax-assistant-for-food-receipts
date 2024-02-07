import os
import re
from collections import defaultdict
import json
import yaml
import time
import math
from loguru import logger
from PIL import Image
import pytesseract
from user_data_handler import UserDataHandler
from pdf_handler import PdfHandler
from OutputHandler import OutputHandler
from chains import Chains


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)


class Main:
    def __init__(self, pdf_file_path=None, data_directory_path=None):
        self.pdf_file_path = pdf_file_path if pdf_file_path is not None else input(
            "Enter PDF source pdf_file_path: ")
        self.data_directory_path = data_directory_path if data_directory_path is not None else input(
            "Enter PDF data_directory_path: ")
        self.logger = logger
        self.logger.add("output.log", level="DEBUG",
                        format="{level}: {message}")

        self.user_data_handler = UserDataHandler(
            logger, self.data_directory_path)
        self.pdf_handler = PdfHandler()
        self.output_handler = OutputHandler
        self.chains = Chains(logger)

        self.processed_images_paths = []
        self.processed_images_text_paths = []
        self.extracted_json_paths = []
        self.extracted_billing_paths = []

        # @TODO: does it make sense to build this into an agent with a testing/correction feature?
        self.extraction_steps = [
            self.chains.BillingDataJson().run,
            self.add_tip,
            self.add_topic,
            self.add_names,
        ]

    def is_pdf(self, file_path):
        _, file_extension = os.path.splitext(file_path)
        return file_extension.lower() == '.pdf'

    def prepare_data_directory(self):
        """Prepare the pdf_file_path structure for processing PDFs:
        Check for validity of file and create data-directory if it doesn't exist.
        """
        try:
            if not os.path.exists(self.data_directory_path):
                os.makedirs(self.data_directory_path)
                self.logger.info(
                    f'Created directory for data extraction: {self.data_directory_path}')
        except OSError as e:
            self.logger.error(
                f"Error creating directory for data extraction for {self.data_directory_path}: {str(e)}")

    """Modifier: adds names to the given text."""

    def add_tip(self, json_data, new_data=None):
        if json_data['tip_amount'] == 0:
            new_data = json_data.copy()
            new_data['tip_percentage'] = 0.1
            new_data['tip_amount'] = round(
                new_data['total_without_tip'] * 0.1, 2)
            new_data['total_with_tip'] = new_data['total_without_tip'] + \
                new_data['tip_amount']
        return new_data or json_data

    """Modifier: adds topic to the given text."""

    def add_topic(self, json_data, new_data=None):
        new_data = json_data.copy()
        new_data['topic'] = f"Projectbesprechung {self.user_data_handler.get_topic()}"
        return new_data

    """Modifier: adds names to the given text."""

    def add_names(self, json_data):
        new_data = json_data.copy()
        total = math.floor(float(json_data["total_with_tip"]))
        name_count = math.floor(
            total / self.user_data_handler.get_billing_value_per_name(total))
        new_data["names"] = self.user_data_handler.get_names_billing_sub_set(
            name_count)
        return new_data

    def run(self, overwrite=False):
        if not os.path.exists(self.pdf_file_path) or not os.path.isfile(self.pdf_file_path) or not self.is_pdf(self.pdf_file_path):
            self.logger.error("The PDF file doesn't exist.")
            exit(1)

        self.prepare_data_directory()
        self.user_data_handler.run()
        self.logger.info(f"Begin processing PDF: {self.pdf_file_path}")

        """Create images from the PDF and save them to the data directory."""
        self.processed_images_paths = self.pdf_handler.create_images_for_pdf(
            self.pdf_file_path, self.data_directory_path)

        def _extract_text_from_image(image_path):
            """
            Extract text from from the image and save it to a text file.
            """
            text_file_path = os.path.splitext(image_path)[0] + ".txt"
            self.processed_images_text_paths.append(text_file_path)
            if not os.path.exists(text_file_path) or overwrite:
                image = Image.open(image_path)
                image_text = pytesseract.image_to_string(image)
                with open(text_file_path, "w") as text_file:
                    self.logger.info(f"Writing text file: {text_file_path}")
                    text_file.write(image_text)

        for processed_images_path in self.processed_images_paths:
            _extract_text_from_image(processed_images_path)

        def _extract_values_to_json(text_path):
            """
            Extract values from the text and save it to a json file.
            """
            json_values_text_path = os.path.splitext(text_path)[0] + ".json"
            self.extracted_json_paths.append(json_values_text_path)

            if not os.path.exists(json_values_text_path) or overwrite:
                with open(processed_image_text_path, "r") as text_file:
                    text_data = text_file.read()

                    output = self.output_handler(text_data)

                    for step in self.extraction_steps:
                        start_time = time.time()
                        step_response = step(output.get_cur())
                        output.add(step_response)
                        end_time = time.time()
                        duration = end_time - start_time
                        self.logger.info(
                            f"Step duration: {duration} seconds" or text_data)

                    with open(json_values_text_path, "w") as billing_text_file:
                        self.logger.info(
                            f"Writing extracted values text file: {json_values_text_path}")
                        json_string = output.encode()
                        billing_text_file.write(json_string)

        for processed_image_text_path in self.processed_images_text_paths:
            _extract_values_to_json(processed_image_text_path)

        def _create_billing_yml(json_file_path: str):
            """
            Create the billing text file.
            """
            billing_text_path = os.path.splitext(json_file_path)[0] + ".yml"
            self.extracted_billing_paths.append(billing_text_path)

            if not os.path.exists(billing_text_path) or overwrite:
                with open(json_file_path, "r") as json_file:
                    json_data = json.load(json_file)
                    data_sets = json_data["data_sets"] or None
                    if data_sets is not None and len(data_sets) > 0:
                        data_set = data_sets[-1]
                        pretty_printed_json = yaml.dump(
                            data_set, allow_unicode=True, sort_keys=False, Dumper=IndentDumper)

                        with open(billing_text_path, "w") as billing_text_file:
                            self.logger.info(
                                f"Writing billing text file: {billing_text_path}")
                            billing_text_file.write(pretty_printed_json)

        for extracted_json_path in self.extracted_json_paths:
            _create_billing_yml(extracted_json_path)


class Secondary(Main):
    def __init__(self, pdf_file_path=None, data_directory_path=None, logger=None):
        super().__init__(pdf_file_path=pdf_file_path,
                         data_directory_path=data_directory_path)
        self.logger = logger

    def get_file_groups(self, directory: str, label_key: str) -> []:
        pattern = re.compile(r"page_(\d+)")

        files_by_index = defaultdict(list)

        for file_name in os.listdir(directory):
            match = pattern.search(file_name)
            if match:
                index = int(match.group(1))
                files_by_index[index].append(
                    os.path.join(directory, file_name))

        return [files_by_index[index]
                for index in sorted(files_by_index)]

    def get_file_sub_group(self, group: [], extensions: []) -> []:
        sub_group = []
        for file in group:
            _, file_extension = os.path.splitext(file)
            if file_extension in extensions:
                sub_group.append(file)
        yield sub_group


if __name__ == "__main__":
    run_id = "essen"
    dest_id = "IBT"  # contained in run_id.
    project_folder = os.path.dirname(os.path.abspath(__file__))
    run_folder = os.path.join(project_folder, run_id)
    dest_folder = os.path.join(run_folder, dest_id)
    app = Main(
        pdf_file_path=f"{run_folder}/IAS-e-q.pdf",
        data_directory_path=dest_folder,
    )
    pdf_processor = Main(
        pdf_file_path=f"{run_folder}/IAS-e-q.pdf",
        data_directory_path=dest_folder,
    )
    pdf_processor.run(overwrite=True)
    pdf_processor.run()

    secondary = Secondary(
        pdf_file_path=f"{run_folder}/IAS-e-q.pdf",
        data_directory_path=dest_folder,
    )
    groups = secondary.get_file_groups(dest_folder, "page_")
    subgroups = []
    for i in range(len(groups)):
        group = groups[i]
        file_extensions = ['.yml', '.png']
        subgroup = next(secondary.get_file_sub_group(group, file_extensions))
        # Reorder the subgroup according to the file extensions in extensions
        subgroup.sort(key=lambda x: file_extensions.index(
            os.path.splitext(x)[1]))
        subgroups.append(subgroup)

    for i in range(len(subgroups)):
        group = subgroups[i]
        secondary.pdf_handler.create_pdf_from_files(
            files=group,
            target=f"{dest_folder}/page_{i}.pdf",
            path_to_signature_image=f"{dest_folder}/signature.png"
        )

        f = 1


# @TODO:
    # post processing:
    # - add a feature to correct the extracted data
    # - add a feature to test name and address
    # - add a feature to test total + tax calculation
    # - add a feature to test tip calculation
    # - test and fix add_names modifier

# @TODO:
    # post-post processing:
    # - add a feature to combine bill-image with billing text into pdf


# @TODO:
    # post processing:
    # - add a feature to correct the extracted data
    # - add a feature to test name and address
    # - add a feature to test total + tax calculation
    # - add a feature to test tip calculation
    # - test and fix add_names modifier

# @TODO:
    # post-post processing:
    # - add a feature to combine bill-image with billing text into pdf

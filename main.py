import os
from loguru import logger
from PIL import Image
import pytesseract

from names_handler import NamesFileHandler
from image_handler import ImageHandler
from extraction_handler import ExtractionHandler

class PDFProcessor:
    def __init__(self, pdf_file_path=None, data_directory_path=None):
        self.pdf_file_path = pdf_file_path if pdf_file_path is not None else input(
            "Enter PDF source pdf_file_path: ")
        self.data_directory_path = data_directory_path if data_directory_path is not None else input(
            "Enter PDF data_directory_path: ")
        self.logger = logger
        self.logger.add("output.log", level="DEBUG", format="{level}: {message}")
        
        self.names_handler = NamesFileHandler(logger, self.data_directory_path)
        self.image_handler = ImageHandler(logger)
        self.extraction_handler = ExtractionHandler(logger, self.names_handler)

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

    def run(self, overwrite=False):
        if not os.path.exists(self.pdf_file_path) or not os.path.isfile(self.pdf_file_path) or not self.is_pdf(self.pdf_file_path):
            self.logger.error("The PDF file doesn't exist.")
            exit(1)

        self.prepare_data_directory()

        self.names_handler.run()

        self.logger.info(f"Begin processing PDF: {self.pdf_file_path}")
        
        """Create images from the PDF and save them to the data directory."""
        processed_images_paths = self.image_handler.create_images_for_pdf(self.pdf_file_path, self.data_directory_path)
        processed_images_text_paths = []
        
        for processed_images_path in processed_images_paths:
            """
            Extract text from from the image and save it to a text file.
            """
            text_file_path = os.path.splitext(processed_images_path)[0] + ".txt"
            processed_images_text_paths.append(text_file_path)
            if not os.path.exists(text_file_path) or overwrite:
                image = Image.open(processed_images_path)
                image_text = pytesseract.image_to_string(image)
                with open(text_file_path, "w") as text_file:
                    self.logger.info(f"Writing text file: {text_file_path}")
                    text_file.write(image_text)
                    
        processed_images_extracted_values_paths = []
        
        for processed_image_text_path in processed_images_text_paths:
            """
            Extract values from the text and save it to a json file.
            """
            json_values_text_path = os.path.splitext(processed_image_text_path)[0] + ".json"
            processed_images_extracted_values_paths.append(json_values_text_path)
            
            if not os.path.exists(json_values_text_path) or overwrite:
                with open(processed_image_text_path, "r") as text_file:
                    text_data = text_file.read()

                    json_string = self.extraction_handler.run(text_data)
                    with open(json_values_text_path, "w") as billing_text_file:
                        self.logger.info(f"Writing extracted values text file: {json_values_text_path}")
                        billing_text_file.write(json_string)


if __name__ == "__main__":
    pdf_processor = PDFProcessor(
        pdf_file_path="/Users/loom23/Sites/ibt-scripts/test/IBT Essen Quittungen 2022.pdf",
        data_directory_path="/Users/loom23/Sites/ibt-scripts/test/IBT Essen Quittungen 2022"
    )
    pdf_processor.run()

import fitz
import os
import logging


class ImageHandler:
    def __init__(self, logger=None):
        self.logger = logger or logging
        self.extracted_images = []

    def create_images_for_pdf(self, file_path: str, target: str, overwrite: bool = False):
        """
        Convert pages of a PDF to images and save them in the target pdf_file_path.

        Args:
            file_path (str): Path to the input PDF file.
            target (str): Directory where the images will be saved.
            overwrite (bool): Flag indicating whether to overwrite existing images. Default is False.
        """
        if os.path.isdir(target) and file_path.endswith('.pdf'):
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                image_path = os.path.join(target, f"page_{i}.png")
                if overwrite or not os.path.exists(image_path):
                    pix.save(image_path)
                    self.logger.info(f'Created image: {image_path}')
                self.extracted_images.append(image_path)
            
        return self.extracted_images

if __name__ == "__main__":
    ImageHandler().create_images_for_pdf()

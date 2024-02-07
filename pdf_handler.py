import os
import logging
import fitz
import yaml


class PdfHandler:
    def __init__(self, logger=None):
        self.fitz = fitz
        self.logger = logger or logging

    def has_key(self, dict, key):
        try:
            dict[key]
            return True
        except KeyError:
            return False

    def get_billing_text(self, data: dict):
        lines = []
        dblnb = '\n\n'
        brktab = '\n\t\t'
        search_keys = ['location_name', 'address', 'currency_code', 'names',
                       'topic', 'total_without_tip', 'tip_amount', 'total_with_tip', 'date',]
        validated_keys = [
            key for key in search_keys if self.has_key(data, key)]
        validated_keys.sort(key=search_keys.index)
        for key in validated_keys:
            try:
                match key:
                    case 'location_name':
                        lines.append(f"Name und Ort der Bewirtung:")
                        lines.append(f"{data['location_name']}")
                        lines.append(f"{data['address']}")
                        lines.append(dblnb)
                    case 'names':
                        lines.append(f"Bewirtende Person:")
                        lines.append(f"{data['names'][0]}")
                        lines.append(dblnb)
                        lines.append(f"Bewirtete Personen:")
                        for name in data['names'][1:]:
                            lines.append(f" - {name}")
                        lines.append(dblnb)
                    case 'topic':
                        lines.append(f"Anlass der Bewirtung:")
                        lines.append(f"{data['topic']}")
                        lines.append(dblnb)
                    case 'total_without_tip':
                        lines.append(
                            f"Höhe der Aufwendungen gemäß beigefügter Rechnung:")
                        total_with_tip = str(data['total_with_tip']).replace(
                            '.', ',')
                        lines.append(
                            f"{total_with_tip} {data['currency_code']} (inkl. MwSt.)")
                        lines.append(dblnb)
                    case 'tip_amount':
                        tip = str(data['tip_amount']).replace('.', ',')
                        lines.append(
                            f"Trinkgeld: {brktab} {tip} {data['currency_code']}")
                        lines.append(dblnb)
                    case 'total_with_tip':
                        total_with_tip = str(data['total_with_tip']).replace(
                            '.', ',')
                        lines.append(
                            f"Gesamtbetrag: {brktab} {total_with_tip} {data['currency_code']}")
                        lines.append(dblnb)
                    case 'date':
                        lines.append(f"Ort, Datum: Berlin, {data['date']}")
                        lines.append(dblnb)
                        lines.append(f"Unterschrift des Bewirtenden:")
            except:
                pass

        return lines

    def replace_text(self, text, search, new_text):
        return text.replace(search, new_text)

    def create_pdf_from_files(self, files: list, target: str, path_to_signature_image: str):
        """
        Combine files to a PDF and save it in the target directory.

        Args:
            files (list): List of image paths.
            target (str): Directory where the PDF will be saved.
            overwrite (bool): Flag indicating whether to overwrite existing PDF. Default is False.
        """

        def _update_pdf_coord(fitz, x, y):
            return fitz.Point(x, y)

        target_dir = os.path.dirname(target)
        if os.path.isdir(target_dir):
            new_doc = self.fitz.open()
            for file in files:
                # if self.fitz can open file, then do so and insert it into doc,
                # otherwise try to read the text in the file
                try:
                    n_pdf = self.fitz.open(file)
                    new_doc.insert_file(n_pdf)
                    n_pdf.close()
                except:
                    with open(file, 'r') as file:
                        data = yaml.safe_load(file)
                        text_lines = self.get_billing_text(data)

                        page = new_doc.new_page()
                        coord = self.fitz.Point(50, 50)

                        page.insert_text(coord,
                                         "Bewirtungsbeleg\n",
                                         fontname="helv",
                                         fontsize=18,
                                         rotate=0,
                                         )
                        page.insert_text(_update_pdf_coord(self.fitz, coord.x, coord.y + 20),
                                         "(nach § 4 Abs. 5 Nr. 2 EStG)",
                                         fontname="helv",
                                         fontsize=10,
                                         rotate=0,
                                         ),
                        page.insert_text(_update_pdf_coord(self.fitz, coord.x, coord.y + 30),
                                         f"Datum: {data['date']}",
                                         fontname="helv",
                                         fontsize=10,
                                         rotate=0,
                                         ),
                        page.insert_text(_update_pdf_coord(self.fitz, coord.x, coord.y + 50),
                                         text_lines,
                                         fontname="helv",
                                         fontsize=12,
                                         rotate=0,
                                         ),
                        page.insert_image(
                            self.fitz.Rect(50, 400, 195, 757),
                            filename=path_to_signature_image,
                        )

            # output_path = os.path.join(target, "output.pdf")
            success = new_doc.save(target)
            new_doc.close()
            return success

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
    pdf_handler = PdfHandler()
    here = os.path.dirname(os.path.abspath(__file__))
    sub_dir = "essen"
    path_to_pages = f"{here}/{sub_dir}/IBT"
    path_to_signature_image = f"{here}/{sub_dir}/IBT/signature.png"
    page_label = "page_7"
    pages_for_pdf = [f"{page_label}.yml", f"{page_label}.png", ]
    paths_to_pages = [os.path.join(path_to_pages, page)
                      for page in pages_for_pdf]
    response = pdf_handler.create_pdf_from_files(
        files=paths_to_pages,
        target=f"{here}/{sub_dir}/{page_label}.pdf",
        path_to_signature_image=path_to_signature_image)
    print(response)

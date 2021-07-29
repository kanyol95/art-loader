import cv2
import json
import numpy as np
import os
from urllib.parse import urlsplit, urlunsplit, quote
from urllib.request import urlopen
import shutil
import time
from typing import Tuple

# Link template as global variable
LINK = 'https://www.wikiart.org/en/App/Search/popular-paintings?searchterm=alltime&json=2&layout=new&layout=new&page={}&resultType=masonry'

# Download the first 10 pages (there are 600 paintings, and on each page there is 60 paintings)
NUM_OF_PAGES = 10

# Define a folder name, which is always unique
FOLDER_NAME = f'_temp_{int(time.time())}'


class Painting:

    def __init__(self, painting_data: dict) -> None:
        self.artist = painting_data['artistName']
        self.title = painting_data['title']
        self.width, self.height, self.image_link = self.select_biggest_image(painting_data)
        self.image = None

        print(f"Next painting: {self.artist} - {self.title}")

    @staticmethod
    def select_biggest_image(painting_data: dict) -> Tuple[int, int, str]:
        # Select the image with the biggest resolution

        # Select the default image first from the painting data
        width = painting_data['width']
        height = painting_data['height']
        image_link = painting_data['image']

        # Check if there are alternative images
        if painting_data['images'] is not None:

            # If there are alternative images, check them one-by-one
            for image in painting_data['images']:

                # Select the image with the biggest resolution
                if image['width'] * image['height'] > width * height:

                    width = image['width']
                    height = image['height']
                    image_link = image['image']

        # Return the data of the biggest image
        return width, height, image_link

    @staticmethod
    def iri2uri(iri):
        # Convert non-ASCII URL to ASCII

        # Create the empty string variable for the uri
        uri = ''

        if isinstance(iri, str):
            # If the variable 'iri' is a string, then we try to split it to parts
            (scheme, netloc, path, query, fragment) = urlsplit(iri)

            # Change the parts of the 'iri' to the proper format
            scheme = quote(scheme)
            netloc = netloc.encode('idna').decode('utf-8')
            path = quote(path)
            query = quote(query)
            fragment = quote(fragment)

            # Join the parts of the 'uri'
            uri = urlunsplit((scheme, netloc, path, query, fragment))

        return uri

    def download_image(self) -> None:
        # Download the painting image

        print("    Downloading...")

        # Download the image
        response = urlopen(self.iri2uri(self.image_link))

        # Convert the raw image to the proper format
        image = np.asarray(bytearray(response.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # Save image as instance attribute
        self.image = image

    def label_image(self) -> None:
        # Label the painting image with artist name and title

        print("    Labeling...")

        # Append a padding to the bottom of the image
        padding_height = int(0.12 * self.height)
        new_img = cv2.copyMakeBorder(self.image, 0, padding_height, 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])

        # Use the following settings as label position and style
        font = cv2.FONT_HERSHEY_SIMPLEX
        painter_position = (10, int(1.05 * self.height))
        title_position = (10, int(1.1 * self.height))
        font_scale = min(self.width, self.height) / 800
        font_color = (255, 255, 255)
        line_type = 2

        # Label the artist
        cv2.putText(new_img, self.artist,
                    painter_position,
                    font,
                    font_scale,
                    font_color,
                    line_type)

        # Label the title
        cv2.putText(new_img, self.title,
                    title_position,
                    font,
                    font_scale,
                    font_color,
                    line_type)

        # Overwrite the original image with the labeled image
        self.image = new_img

    def save_image(self) -> None:
        # Save the image to a temporary folder

        # Define the save name from the image link
        save_name = self.image_link.split('/')[-1]

        # Write the image to the folder
        cv2.imwrite(f'{FOLDER_NAME}/{save_name}', self.image)

        print("    Painting saved!")

    def load_label_save(self) -> None:
        # Run the entire process

        # Run all the functions
        self.download_image()
        self.label_image()
        self.save_image()


def main() -> None:
    # The main program

    # Create temporary folder (this way it have to be unique)
    os.mkdir(FOLDER_NAME)

    # Loop for NUM_OF_PAGES cycles
    for i in range(1, NUM_OF_PAGES + 1):

        # Load data as JSON
        resp = urlopen(LINK.format(i))
        data = json.loads(resp.read().decode("utf-8"))

        # Loop on loaded JSON data
        for painting_data in data['Paintings']:

            # Check the attributes of the painting, download, label and save it
            painting = Painting(painting_data)
            painting.load_label_save()

    # Zip the collected paintings
    shutil.make_archive('LABELED_PAINTINGS', 'zip', FOLDER_NAME)

    # Remove the unzipped data
    shutil.rmtree(FOLDER_NAME)


if __name__ == "__main__":

    # Run the main program
    main()

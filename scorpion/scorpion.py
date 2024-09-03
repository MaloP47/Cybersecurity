import sys
from PIL import Image
from PIL.ExifTags import TAGS


def printExif(file):
    try:
        img = Image.open(file)
        data = img._getexif()
        if data is not None:
            print(f"EXIF data for {file}:")
            for tag, value in data.items():
                tag_name = TAGS.get(tag, tag)
                print(f"{tag_name}: {value}")
        else:
            print(f"No EXIF data found for {file}")
    except Exception as e:
        print(f"Error processing {file}: {e}")


def main():
    try:
        if len(sys.argv) >= 2:
            for file in sys.argv[1:]:
                printExif(file)
                print('************************************')
        else:
            print("Add a path! EXAMPLE: python scorpion.py ../img/animal.jpg")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

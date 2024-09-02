from load_image import ft_load
import sys
from PIL import Image
from PIL.ExifTags import TAGS


def main():
    try:
        if len(sys.argv) == 2:
            # print(ft_load(sys.argv[1]))
            img = ft_load(sys.argv[1])
            # img.show()
            file = sys.argv[1]
            data = img._getexif()
            if data is not None:
                print(f"EXIF data for {file}:")
                for tag, value in data.items():
                    tag_name = TAGS.get(tag, tag)
                    print(f"{tag_name}: {value}")
            else:
                print(f"No EXIF data found for {file}")
        else:
            print("EXAMPLE")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

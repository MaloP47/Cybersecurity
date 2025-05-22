import argparse
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def is_valid_image_url(url):
    """Check if the URL points to an image with valid extension."""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    return any(
        url.lower().endswith(ext)
        for ext in valid_extensions
    )


def download_image(url, save_path):
    """Download an image from the URL and save it to the specified path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Get filename from URL
        filename = os.path.basename(urlparse(url).path)
        if not filename:
            filename = 'image_' + str(hash(url)) + '.jpg'

        # Create save path if it doesn't exist
        os.makedirs(save_path, exist_ok=True)

        # Save the image
        file_path = os.path.join(save_path, filename)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def extract_images_from_page(url, save_path, visited_urls=None, depth=0,
                             max_depth=None):
    """Extract and download images from a webpage recursively."""
    if visited_urls is None:
        visited_urls = set()

    if url in visited_urls:
        return

    if max_depth is not None and depth > max_depth:
        return

    visited_urls.add(url)
    print(f"\033[32mVisiting: {url}\033[0m")  # Print URL in green

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all image tags
        for img in soup.find_all('img'):
            img_url = img.get('src')
            if img_url:
                # Convert relative URL to absolute URL
                img_url = urljoin(url, img_url)
                if is_valid_image_url(img_url):
                    download_image(img_url, save_path)

        # Only follow links if we haven't reached max depth
        if max_depth is None or depth < max_depth:
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    next_url = urljoin(url, href)
                    # Only follow links from the same domain
                    if (urlparse(next_url).netloc == urlparse(url).netloc):
                        extract_images_from_page(
                            next_url, save_path, visited_urls,
                            depth + 1, max_depth
                        )

    except Exception as e:
        print(f"Error processing {url}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Image Scraper',
        usage='./spider [-rlp] URL'
    )
    parser.add_argument(
        '-r', action="store_true",
        help="recursively download images"
    )
    parser.add_argument(
        '-l', type=int, default=5,
        metavar='[N]', help='recursive depth'
    )
    parser.add_argument(
        '-p', type=str, default='./data/',
        metavar='[PATH]', help='save path'
    )
    parser.add_argument('URL', type=str, help='Url to scrape')

    args = parser.parse_args()

    # Only check for -l if it was explicitly set by the user
    if args.l != 5 and not args.r:
        parser.error('Use -l with -r')

    try:
        if args.r:
            # If -l is specified, use that value, otherwise use default 5
            max_depth = args.l if args.l != 5 else 5
            extract_images_from_page(args.URL, args.p, max_depth=max_depth)
        else:
            # Single page mode
            extract_images_from_page(args.URL, args.p, max_depth=0)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.exceptions import Timeout, HTTPError, RequestException


def testUrl(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except (ConnectionError, Timeout, HTTPError) as e:
        print(f"Error : {e}")
    except RequestException as e:
        print(f"Error : {e}")
    # return response


def main():

    parser = argparse.ArgumentParser(description='Img Scrapper', usage='./spider [-rlp] URL')
    parser.add_argument('-r', action="store_true", help="default : false")
    parser.add_argument('-l', type=int, default=5, metavar='[N]', help='recursive depth')
    parser.add_argument('-p', type=str, default='../img', metavar='[PATH]', help='save path')
    parser.add_argument('URL', type=str, help='Url to scrap')

    args = parser.parse_args()

    if args.l and not args.r:
        parser.error('Use -l with -r')
    try:
        testUrl(args.URL)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()

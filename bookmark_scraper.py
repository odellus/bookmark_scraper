# -*- coding: utf-8


import json
import os
import urllib3
import copy

from bs4 import BeautifulSoup
from tqdm import tqdm

def get_pool_manager(
    num_pools=10,
    user_agent={"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"}
    ):
    return urllib3.PoolManager(num_pools=num_pools, headers=user_agent)

def load_json(fpath):
    """
    """
    with open(fpath, "r") as f:
        return json.load(f)

def dump_json(obj, fpath):
    """
    """
    with open(fpath, "w") as f:
        json.dump(obj, f)

def get_bookmarks(bookmark_path=".config/google-chrome/Default/Bookmarks"):
    """
    """
    home_dir = os.environ["HOME"]
    abs_bookmark_path = "/".join([home_dir, bookmark_path])
    return load_json(abs_bookmark_path)

def is_folder(element):
    """
    """
    if element['type'] == 'folder':
        return True
    else:
        return False

def process_children(bookmarks, bookmark_list):
    if not is_folder(bookmarks):
        return bookmark_list.append(bookmarks)
    else:
        for child in bookmarks['children']:
            if is_folder(child):
                tmp_bookmarks = process_children(child, bookmark_list)
                bookmark_list.extend(tmp_bookmarks)
            else:
                bookmark_list.append(child)
        return bookmark_list

def get_urls(bookmark_dict):
    bookmark_list = []
    b_root = bookmark_dict['roots']
    for folder in b_root:
        for children in b_root[folder]['children']:
            tmp_bookmarks = process_children(children, bookmark_list)
    return bookmark_list


def fetch_bookmark_urls():
    bookmarks = get_bookmarks()
    return get_urls(bookmarks)


def get_soup(http, url):
    if url.endswith(".pdf"):
        return None
    r = http.urlopen("GET", url, retries=999)
    return BeautifulSoup(r.data, "html.parser")

def get_links(http, url):
    soup = get_soup(http, url)
    if soup is None:
        return []
    else:
        return [x.href for x in soup.find_all("a")]

def get_text(http, url):
    soup = get_soup(http, url)
    if soup is None:
        return ""
    else:
        return soup.get_text()

def traverse_bookmarks(bookmarks, http):
    augmented_bookmarks = []
    for bookmark in tqdm(bookmarks):
        better_bookmark = copy.copy(bookmark)
        url = bookmark["url"]
        name = bookmark["name"]
        text = get_text(http, url)
        links = get_links(http, url)
        better_bookmark["text"] = text
        better_bookmark["links"] = links
        augmented_bookmarks.append(better_bookmark)

    return augmented_bookmarks


def main(first_k=None, serialize=False):
    http = get_pool_manager()
    bookmarks = fetch_bookmark_urls()
    if first_k is not None:
        bookmarks = bookmarks[:first_k]
    augmented_bookmarks = traverse_bookmarks(bookmarks, http)
    output_json = {"augmented": augmented_bookmarks}
    output_fpath = "augmented_bookmarks.json"
    if serialize:
        dump_json(output_json, output_fpath)
    return output_json

if __name__ == "__main__":
    main(serialize=True)

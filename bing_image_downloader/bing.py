from pathlib import Path
import urllib.request
import urllib
import imghdr
import posixpath
import re
import json

'''
Python api to download image form Bing.
Author: Guru Prasad (g.gaurav541@gmail.com)
'''


class Bing:
    def __init__(self, query, limit, output_dir, adult, timeout,  filter='', max_empty_pages=500, verbose=True):
        self.download_count = 0
        self.query = query
        self.output_dir = output_dir
        self.adult = adult
        self.filter = filter
        self.verbose = verbose
        self.seen = set()
        self.link_dict = {}
        self.max_empty_pages = max_empty_pages

        assert type(limit) == int, "limit must be integer"
        self.limit = limit
        assert type(timeout) == int, "timeout must be integer"
        self.timeout = timeout

        # self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'}
        self.page_counter = 0
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
      'AppleWebKit/537.11 (KHTML, like Gecko) '
      'Chrome/23.0.1271.64 Safari/537.11',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
      'Accept-Encoding': 'none',
      'Accept-Language': 'en-US,en;q=0.8',
      'Connection': 'keep-alive'}


    def get_filter(self, shorthand):
            if shorthand == "line" or shorthand == "linedrawing":
                return "+filterui:photo-linedrawing"
            elif shorthand == "photo":
                return "+filterui:photo-photo"
            elif shorthand == "clipart":
                return "+filterui:photo-clipart"
            elif shorthand == "gif" or shorthand == "animatedgif":
                return "+filterui:photo-animatedgif"
            elif shorthand == "transparent":
                return "+filterui:photo-transparent"
            else:
                return ""


    def save_image(self, link, file_path):
        request = urllib.request.Request(link, None, self.headers)
        image = urllib.request.urlopen(request, timeout=self.timeout).read()
        if not imghdr.what(None, image):
            print('[Error]Invalid image, not saving {}\n'.format(link))
            raise ValueError('Invalid image, not saving {}\n'.format(link))
        with open(str(file_path), 'wb') as f:
            f.write(image)

    
    def download_image(self, link):
        self.download_count += 1
        # Get the image link
        try:
            path = urllib.parse.urlsplit(link).path
            filename = posixpath.basename(path).split('?')[0]
            file_type = filename.split(".")[-1]
            if file_type.lower() not in ["jpe", "jpeg", "jfif", "exif", "tiff", "gif", "bmp", "png", "webp", "jpg"]:
                file_type = "jpg"
                
            last_url = link.rsplit('/', 1)[-1]
            file_name = f"IMG_{self.download_count:05d}_{last_url}"
            file_path = self.output_dir.joinpath(file_name)
    
            if self.verbose:
                # Download the image
                print("Downloading #{} from {} to {}".format(self.download_count, link, file_name))
                

            self.link_dict[file_name]=link
            self.save_image(link, file_path)
            #if self.verbose:
            #    print("[%] File Downloaded!")

        except Exception as e:
            self.download_count -= 1
            print("[!] Issue getting: {}\n[!] Error:: {}".format(link, e))

    
    def run(self):
        empty_page_count = 0
        while (self.download_count < self.limit) and (empty_page_count <= self.max_empty_pages):
            if self.verbose:
                print("===============================================")
                print("empty_page_count", empty_page_count)
                print('[!!]Indexing page: {}'.format(self.page_counter + 1))
            # Parse the page source and download pics
            request_url = 'https://www.bing.com/images/async?q=' + urllib.parse.quote_plus(self.query) \
                          + '&first=' + str(self.page_counter) + '&count=' + str(self.limit) \
                          + '&adlt=' + self.adult + '&qft=' + ('' if self.filter is None else self.get_filter(self.filter))
            try:
                request = urllib.request.Request(request_url, None, headers=self.headers)
                response = urllib.request.urlopen(request)
                html = response.read().decode('utf8')
                if html ==  "":
                    print("[%] No more images are available.")
                    break
                links = re.findall('murl&quot;:&quot;(.*?)&quot;', html)
                if self.verbose:
                    print("[%] Indexed {} Images on Page {}.".format(len(links), self.page_counter + 1))

                empty_page = True
                for link in links:
                    if self.download_count < self.limit and link not in self.seen:
                        self.seen.add(link)
                        self.download_image(link)
                        empty_page = False
                        empty_page_count = 0
                empty_page_count += empty_page

            except:
                print("Err for", request_url)

            self.page_counter += 1
        print("[%] Done. Downloaded {} images.".format(self.download_count))

        dict_file = f'{self.output_dir}.json'
        print(self.link_dict)
        with open(dict_file, 'w') as fp:
            json.dump(self.link_dict, fp)
        print(f"Dict_file saved in {dict_file}.")

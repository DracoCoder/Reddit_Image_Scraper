import os
import praw
import configparser
import urllib.request
from tqdm import tqdm
from time import sleep

from prawcore.exceptions import Redirect
from prawcore.exceptions import ResponseException
from urllib.error import HTTPError


class ClientInfo:
    id = ''
    secret = ''
    user_agent = 'Reddit_Image_Scraper'


def get_client_info():
    config = configparser.ConfigParser()
    config.read("config.ini")
    id = config["ALPHA"]["client_id"]
    secret = config["ALPHA"]["client_secret"]

    return id, secret


def is_img_link(img_link):
    return img_link.lower().endswith("jpg") or img_link.lower().endswith("png") or img_link.lower().endswith("gif")

def save_list(img_url_list):
    for img_url in img_url_list:
        if not is_img_link(img_url):
            continue
        file = open('img_links.txt', 'a')
        file.write('{} \n'.format(img_url))
        file.close()


def delete_img_list():
    f = open('img_links.txt', 'r+')
    f.truncate()


def get_img_urls(sub, li):
    try:
        r = praw.Reddit(client_id=ClientInfo.id, client_secret=ClientInfo.secret, user_agent=ClientInfo.user_agent)
        if hot:
            submissions = r.subreddit(sub).hot(limit=li*5)
        else:
            submissions = r.subreddit(sub).top(time_filter="all", limit=li*5)

        return [submission.url for submission in submissions]

    except Redirect:
        print("Invalid Subreddit!")
        return 0

    except HTTPError:
        print("Too many Requests. Try again later!")
        return 0

    except ResponseException:
        print("Client info is wrong. Check again.")
        return 0

    except Exception as e:
        print("Unexpected Error:", e)
        return 0


def download_img(img_url, img_title, filename):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        # print('Downloading ' + img_title + '....')
        urllib.request.urlretrieve(img_url, filename)
        return 1

    except HTTPError as e:
        print("Too many Requests. Try again later!, ", e)
        return 0

    except OSError as e:
        print("OSError:", e)
        return 0

    except Exception as e:
        print("Unexpected Error:", e)
        return 0

def read_img_links(sub, limit, tolerance=3):
    failed = 0
    with open('img_links.txt') as f:
        links = f.readlines()

    links = [x.strip() for x in links]
    download_count = 0

    for link in tqdm(links, total=limit):
        if not is_img_link(link):
            continue

        if(download_count == limit):
            return download_count, 1

        file_name = link.split('/')[-1]
        file_loc = 'result/{}/{}'.format(sub, file_name)

        directory = os.path.dirname('result/{}/'.format(sub))
        if not os.path.exists(directory):
            os.makedirs(directory)

        if not file_name:
            continue

        download_status = download_img(link, file_name, file_loc)
        sleep(3)

        if download_status == 0:
            failed+=1
            if(failed==tolerance):
                return download_count, 0
            continue
        else:
            download_count += 1

    return download_count, 1


if __name__ == '__main__':

    ClientInfo.id, ClientInfo.secret = get_client_info()

    subreddit = input('Enter Subreddit: ')
    hot = bool(input('0 For Top, 1 For Hot: '))
    limit = int(input('Enter Limit: '))
    url_list = get_img_urls(subreddit, limit)

    if url_list:

        save_list(url_list)
        count, status = read_img_links(subreddit, limit)

        if status == 1:
            print(f'\nDownload Complete\n{count} - Images Downloaded.')
        elif status == 0:
            print('\nDownload Incomplete\n{} - Images Downloaded'.format(count))

    delete_img_list()

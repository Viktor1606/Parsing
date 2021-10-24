# 563492ad6f917000010000017144375653184541a512592a3d23007b

import requests
from pprint import pprint
def download(q: str, p:str):
    header = {"Authorization": "563492ad6f917000010000017144375653184541a512592a3d23007b"}
    i = 1
    while i <= int(p):
        url = f"https://api.pexels.com/v1/search?query={q}&per_page=1&page{i}"
        req = requests.get(url, headers=header)
        if req.ok == True:
            r = req.json()
            print(r)
            for item in r.get("photos"):
                print(item.get("url"))
        else:
            print(req.text)
        i += 1

def main() -> None:
    q = input("Введите слово: ")
    p = input("Введите колличество: ")
    download(q, p)

main()
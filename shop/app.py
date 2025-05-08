import time
import json
import socket
import multiprocessing
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def getInfo(mid, keyword):
    rank = -1
    data = {'rank': rank, 'item_name': '', 'img_url': ''}

    options = Options()
    # options.add_argument('--headless=new')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--disable-gpu')
    


    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        for pagingIndex in range(1, 4):
            shopping_link = f"https://msearch.shopping.naver.com/search/all?frm=NVSHATC&pagingIndex={pagingIndex}&pagingSize=40&productSet=total&query={keyword}&sort=rel&timestamp=&viewType=list"
            driver.get(shopping_link)
            time.sleep(0.5)
            driver.execute_script("window.scrollBy(0,10000);")
            time.sleep(0.5)

            try:
                # [1] 상품 블록 찾기
                product_div = driver.find_element(By.ID, f"_sr_lst_{mid}")

                # [2] 순위 추출
                rank_element = product_div.find_element(By.CSS_SELECTOR, f"a[data-i='{mid}']")
                rank = rank_element.get_attribute("data-shp-contents-rank")
                print(f"[{mid}] rank={rank}")

                # [3] 이미지 URL 추출
                img_element = product_div.find_element(By.CSS_SELECTOR, "img")
                img_src = img_element.get_attribute("src")
                print(f"[{mid}] img_src={img_src}")

                # [4] 상품명 추출
                name_element = product_div.find_element(By.CSS_SELECTOR, "span.product_info_tit__UOCqq")
                name = name_element.text
                print(f"[{mid}] name={name}")

                data = {'rank': rank, 'item_name': name, 'img_url': img_src}
                break

            except Exception as e:
                print(f"[{keyword} mid:{mid}] {pagingIndex} 페이지에서 상품을 찾지 못했습니다.")
    finally:
        driver.quit()

    return data

def binder(client_socket, addr):
    print('Connected by', addr)
    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            data = json.loads(data)
            mid = data["mid"]
            keyword = data["keyword"]
            print("addr:", addr, "keyword:", keyword)

            msg = getInfo(mid, keyword)
            print("msg:", msg)

            jd = json.dumps(msg)
            data = jd.encode()
            length = len(data)

            client_socket.sendall(length.to_bytes(4, byteorder="little"))
            client_socket.sendall(data)

    except Exception as e:
        print("except:", addr, e)
    finally:
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', 9999))
    server_socket.listen()

    try:
        while True:
            client_socket, addr = server_socket.accept()
            p = multiprocessing.Process(target=binder, args=(client_socket, addr))
            p.start()
    except Exception as e:
        print("server error:", e)
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()
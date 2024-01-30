import time
import json
import socket
import multiprocessing
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
# from pyvirtualdisplay import Display


# from selenium.webdriver import ChromeOptions
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service as ChromeService
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# display = Display(visible=0, size=(1920, 1080))
# display.start()


options = Options()
options.add_experimental_option("detach", True)
# 창 숨기는 옵션 추가
user_agent=f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
options.add_argument(user_agent)
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# service = Service(executable_path='/home/ubuntu/chromedriver-linux64/chromedriver')
# driver = webdriver.Chrome(service=service, options=options)


def getInfo(mid, keyword):
    rank = -1
    data = {'rank': rank, 'item_name': '', 'img_url': ''}
    for pagingIndex in range(1,4):
        
        # step(1) 사이트 접속하기
        shopping_link = f"https://msearch.shopping.naver.com/search/all?frm=NVSHATC&pagingIndex={pagingIndex}&pagingSize=40&productSet=total&query={keyword}&sort=rel&timestamp=&viewType=list"
        driver.get(shopping_link)
        time.sleep(0.5)
        # step(2) 페이지를 하단으로 내리기 (모바일버전 상품 더 불러오기)
        driver.execute_script("window.scrollBy(0,10000);")
        time.sleep(0.5)
        
      
        # step(3) 타겟상품이 페이지에 노출되고 있는지 확인하기 
        # step(4) 없다면 -> url로 next page  
        try: 
            # 상품 등수 찾기
            target_rank_selector = f"a[data-i='{mid}']"
            rank_element = driver.find_element(By.CSS_SELECTOR, target_rank_selector)
            rank_data = rank_element.get_attribute('data-nclick')
            rank = rank_data.split(f"{mid},r:")[-1].split(",")[0]
            print(f"rank = {rank} keyword = {keyword}")
            # 상품 이미지주소 찾기
            target_img_selector = f"//*[@id='_sr_lst_{mid}']/div/div[1]/span/img"
            img_element = driver.find_element(By.XPATH, target_img_selector)
            img_src = img_element.get_attribute('src')
            print(f"img_src = {img_src} keyword = {keyword}")
            # 상품 이름 찾기 
            target_name_selector = f"//*[@id='_sr_lst_{mid}']/div/div[1]/div/span"
            name_element = driver.find_element(By.XPATH, target_name_selector)
            name = name_element.text
            print(f"name = {name} keyword = {keyword}")
            data = {'rank': rank, 'item_name': name, 'img_url': img_src}
            break     
        except Exception as e: 
            print(f"{pagingIndex} 페이지에서 타겟 상품을 찾지 못함")
            # 다음페이지로 이동 필요 
        finally: 
            # driver.close
            driver.quit
           
    return data
    

# binder함수는 서버에서 accept가 되면 생성되는 socket 인스턴스를 통해 client로 부터 데이터를 받으면 json형태로 재송신하는 메소드이다.
def binder(client_socket, addr):
  # 커넥션이 되면 접속 주소가 나온다.
  print('Connected by', addr)
  try:    
    # 접속 상태에서는 클라이언트로 부터 받을 데이터를 무한 대기한다.
    # 만약 접속이 끊기게 된다면 except가 발생해서 접속이 끊기게 된다.
    while True:
        data = client_socket.recv(1024).decode()
        # print('data', data)

        data = json.loads(data)
        # print('json data', data)

        # 수신된 mid와 keyword 정의 
        mid = data["mid"]
        keyword = data["keyword"]
        # print("mid : " , mid)
        print("addr : " , addr," keyword : " , keyword)

        # 수신된 mid와 keyword로 크롤링 
        msg = getInfo(mid, keyword)
        print("msg : " , msg)

        # 바이너리(byte)형식으로 변환한다.
        jd = json.dumps(msg)
        print("jd : " , jd)
        data = jd.encode()
        # 바이너리의 데이터 사이즈를 구한다.
        length = len(data)

        #새로운 자료형 확인하기
        # print(type(data))
        # print(length)

        # 데이터 사이즈를 little 엔디언 형식으로 byte로 변환한 다음 전송한다.
        client_socket.sendall(length.to_bytes(4, byteorder="little"))
        
        # 데이터를 클라이언트로 전송한다
        client_socket.sendall(data)
  except:
    # 접속이 끊기면 except가 발생한다.
    print("except : " , addr)
  finally:
    # 접속이 끊기면 socket 리소스를 닫는다.
    client_socket.close()
    
def main():
    # 소켓을 만든다.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 소켓 레벨과 데이터 형태를 설정한다.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 서버는 복수 ip를 사용하는 pc의 경우는 ip를 지정하고 그렇지 않으면 None이 아닌 ''로 설정한다.
    # 포트는 pc내에서 비어있는 포트를 사용한다. cmd에서 netstat -an | find "LISTEN"으로 확인할 수 있다.
    server_socket.bind(('', 9999))
    # server 설정이 완료되면 listen를 시작한다.
    server_socket.listen()

    try:
        # 서버는 여러 클라이언트를 상대하기 때문에 무한 루프를 사용한다.
        while True:
            # client로 접속이 발생하면 accept가 발생한다.
            # 그럼 client 소켓과 addr(주소)를 튜플로 받는다.
            client_socket, addr = server_socket.accept()
            # 쓰레드를 이용해서 client 접속 대기를 만들고 다시 accept로 넘어가서 다른 client를 대기한다.
            processes = []
            p = multiprocessing.Process(target=binder, args = (client_socket,addr))
            p.start() # process 시작
            
            processes.append(p)
        
            # for process in processes:
            #     process.join() # process 작업 끝날 때까지 기다리기
                
        
    except:
        print("server")
    finally:
    # 에러가 발생하면 서버 소켓을 닫는다.
        server_socket.close()


if __name__ == '__main__':
    main()
import requests
from bs4 import BeautifulSoup
from random import randint
import pandas as pd
import easyocr
import os
import warnings
from time import sleep


class Crawl:
    def __init__(self, login_id: str, login_pw: str):
        self.login_id = login_id
        self.login_pw = login_pw
        self.table_names = ['corona', 'student_notice', 'subject', 'sunrise', 'sunrise_post', 'qa', 'domestic', 'rule',
                            'club_study', 'lost_and_found', 'student_club', 'student_project', 'student_self',
                            'student_subject', 'student_jisikin', 'student']
        self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
                'Accept'    : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"}
        self.session = self.get_login_session()
        self.reader = easyocr.Reader(['ko', 'en'])

    def get_login_session(self):
        print("get session")
        session = requests.Session()
        session.headers.update(self.headers)

        url_login_page = 'https://hi.hana.hs.kr/member/login.asp'
        session.get(url_login_page)

        url_login_proc = 'https://hi.hana.hs.kr/proc/login_proc.asp'
        login_data = {'login_id': self.login_id, 'login_pw': self.login_pw, 'x': str(randint(10, 99)),
                      'y'       : str(randint(10, 99))}
        session.post(url_login_proc, headers={'Referer': url_login_page}, data=login_data)
        return session

    def get_posts_urls(self, board_name: str, page: int, end_date: str = ""):
        url_dict = {
                'corona'         : f'https://hi.hana.hs.kr/SYSTEM_Community/Board/Corona_Board/Corona.asp?mode=list&page={page}&code=0650&searchopt=&searchkey=',
                'student_notice' : f'https://hi.hana.hs.kr/SYSTEM_Community/Board/Student_notice_Board/student_notice.asp?mode=list&page={page}&code=0610&searchopt=&searchkey=',
                'subject'        : f"https://hi.hana.hs.kr/SYSTEM_Community/Board/Subject_Board/subject.asp?mode=list&page={page}&code=0611&searchopt=&searchkey=&category=",
                'sunrise'        : f'https://hi.hana.hs.kr/SYSTEM_Community/Board/sunrise_board/sunrise.asp?mode=list&page={page}&code=0613&searchopt=&searchkey=',
                'sunrise_post'   : f'https://hi.hana.hs.kr/SYSTEM_Community/Board/sunrisePost_board/sunrisePost.asp?mode=list&page={page}&code=0633&searchopt=&searchkey=',
                'qa'             : f'https://hi.hana.hs.kr/SYSTEM_Community/Board/QA_Board/qa.asp?mode=list&page={page}&code=0310&searchopt=&searchkey=',
                'domestic'       : f"https://hi.hana.hs.kr/SYSTEM_SchoolLife/Admission_Info/Admission_Domestic/domestic.asp?mode=list&page={page}&code=0205&searchopt=&searchkey=",
                'rule'           : f'https://hi.hana.hs.kr/SYSTEM_Community/Board/Rule_Board/rule.asp?mode=list&page={page}&code=0625&searchopt=&searchkey=',
                'club_study'     : f"https://hi.hana.hs.kr/SYSTEM_Community/Board/clubstudy_Board/clubstudy.asp?mode=list&page={page}&code=0622&searchopt=&searchkey=&category=",
                'lost_and_found' : f"https://hi.hana.hs.kr/SYSTEM_SchoolLife/Student_Life/Lost_and_Found/lostandfound.asp?mode=list&page={page}&code=0606&searchopt=&searchkey=&category=",
                'student_club'   : f"https://hi.hana.hs.kr/SYSTEM_Community/Board/Student_Club/student.asp?mode=list&page={page}&code=0661&searchopt=&searchkey=",
                'student_project': f"https://hi.hana.hs.kr/SYSTEM_Community/Board/Student_Project/student.asp?mode=list&page={page}&code=0662&searchopt=&searchkey=",
                'student_self'   : f"https://hi.hana.hs.kr/SYSTEM_Community/Board/Student_Self/student.asp?mode=list&page={page}&code=0663&searchopt=&searchkey=",
                'student_subject': f"https://hi.hana.hs.kr/SYSTEM_Community/Board/Student_Self/student.asp?mode=list&page={page}&code=0663&searchopt=&searchkey=",
                'student_jisikin': f"https://hi.hana.hs.kr/SYSTEM_Community/Board/Student_Jisikin/student.asp?mode=list&page={page}&code=0665&searchopt=&searchkey=",
                'student'        : f"https://hi.hana.hs.kr/SYSTEM_Community/Board/Student_Board/student.asp?mode=list&page={page}&code=0603&searchopt=&searchkey="

        }
        url = url_dict[board_name]

        # HTTP GET 요청
        while True:
            try:
                response = self.session.get(url)
                if "정상적인 로그아웃이 되지 않았습니다." in response.text or "비정상적인 로그인 시도로 정보가 초기화 되었습니다." in response.text:
                    sleep(10)
                    self.session = self.get_login_session()
                    continue
                break

            except Exception as e:
                print(e)
                sleep(10)
                self.session = self.get_login_session()
                continue

        html_data = response.text

        # BeautifulSoup로 HTML 파싱
        soup = BeautifulSoup(html_data, 'html.parser')

        # 테이블 요소 찾기
        table = soup.find('table', {'class': 'board_list_general'}) or soup.find('table',
                                                                                 {'class': 'board_list_lostcenter'})

        # 데이터 저장을 위한 리스트 초기화
        data = []

        if table is None:
            return None

        for row in table.find('tbody').find_all('tr'):
            category = 'normal'
            num_td = row.find_all('td', {'class': 'num'})[-1]

            if num_td.find('img', {'src': '/_images/board/lost_1.gif'}):
                category = '찾습니다'
            elif num_td.find('img', {'src': '/_images/board/lost_2.gif'}):
                category = '찾아가세요'
            elif num_td.find('img', {'src': '/_images/board/lost2_1.gif'}):
                category = '대회/행사'
            elif num_td.find('img', {'src': '/_images/board/lost2_2.gif'}):
                category = '교과학습'
            elif num_td.find('img', {'src': '/_images/board/lost3_1.gif'}):
                category = '집현'
            elif num_td.find('img', {'src': '/_images/board/lost3_2.gif'}):
                category = '동아리'
            elif num_td.find('img', {'src': '/hanaBBS_skin/bbs/bbsQna/image/reply_wait.gif'}):
                category = '답변 대기중'
            elif num_td.find('img', {'src': '/hanaBBS_skin/bbs/bbsQna/image/reply_complete.gif'}):
                category = '답변 완료'
            else:
                category = 'normal'

            if row.find_all('td', {'class': 'num'})[0].find('img', {'src': '/_images/board/icon_notice.gif'}):
                if page > 1:
                    continue
                category = 'notice'
                post_id = None
            else:
                post_id = row.find_all('td', {'class': 'num'})[0].get_text()

            link = row.find('a')['href']
            writer = row.find('td', {'class': 'writer'}).get_text()
            date = row.find('td', {'class': 'date'}).get_text()
            hit = row.find('td', {'class': 'hit'}).get_text()

            if date < end_date and category != "notice":
                break

            data.append({
                    'post_id'   : post_id,
                    'board_name': board_name,
                    'category'  : category,
                    'link'      : url.split('?')[0] + link,
                    'writer'    : writer,
                    'date'      : date,
                    'hit'       : hit
            })

        if len(data) == 0:
            return None

        # pandas DataFrame으로 변환
        df = pd.DataFrame(data)

        return df

    def get_post_details(self, url: str):
        # HTTP GET 요청
        while True:
            try:
                response = self.session.get(url)
                if "정상적인 로그아웃이 되지 않았습니다." in response.text or "비정상적인 로그인 시도로 정보가 초기화 되었습니다." in response.text:
                    sleep(10)
                    self.session = self.get_login_session()
                    continue
                break
            except Exception as e:
                print(e)
                sleep(10)
                self.session = self.get_login_session()
                continue

        html_data = response.text

        # BeautifulSoup로 HTML 파싱
        soup = BeautifulSoup(html_data, 'html.parser')

        # 데이터 저장을 위한 리스트 초기화
        data = []

        # 게시글 제목
        title = soup.find('th', {'class': 'subject'}).get_text()

        # 게시글 작성자, 날짜, 조회수
        writer = soup.find('td', {'class': 'writer_form'}).get_text()
        date = soup.find('td', {'class': 'date_form'}).get_text()
        hit = soup.find('td', {'class': 'hit_form'}).get_text()

        # 게시글 내용
        content_div = soup.find('td', {'class': 'board_content'}).find('div', {'class': 'content'})
        content_text = content_div.get_text(separator="\n", strip=True)

        # 이미지 URL 추출
        images = [img['src'] for img in content_div.find_all('img')]

        # 첨부파일 URL 추출
        attachments = []
        for file_link in content_div.find_all('a', {'title': '파일 다운로드'}):
            file_url = file_link['href']
            file_name = file_link.get_text(strip=True)
            attachments.append({'file_name': file_name, 'file_url': file_url})

        # 이미지 ocr
        images = [img for img in images if img.startswith('https://hi.hana.hs.kr/common/downloadEditFile.asp?img=')]
        image_texts = []
        images_base64 = []

        for i, img_url in enumerate(images):
            try:
                img_response = self.session.get(img_url)
                img_path = f"temp_image_{i}.png"
                with open(img_path, 'wb') as f:
                    f.write(img_response.content)

                # easyocr을 사용하여 이미지에서 텍스트 추출
                result = self.reader.readtext(img_path, detail=0)
                image_text = " ".join(result)
                image_texts.append(image_text)

                # # 이미지를 base64로 인코딩
                # with open(img_path, 'rb') as f:
                #     if img_url.lower().endswith('.png'):
                #         img_base64 = f"data:image/png;base64,{f.read().hex()}"
                #     elif img_url.lower().endswith('.jpg') or img_url.lower().endswith('.jpeg'):
                #         img_base64 = f"data:image/jpeg;base64,{f.read().hex()}"
                #     else:
                #         img_base64 = ""
                #     images_base64.append(img_base64)

                # 임시 이미지 파일 삭제
                os.remove(img_path)
            except Exception as e:
                print(e)
                image_texts.append("")

        # 이미지에서 추출한 텍스트를 콘텐츠에 추가
        content_images = "\n\n".join(image_texts)

        # 데이터 리스트에 추가
        data.append({
                'title'         : title,
                'writer'        : writer,
                'date'          : date,
                'hit'           : hit,
                'content_text'  : content_text,
                'content_images': content_images,
                'images'        : images,
                # 'images_base64' : images_base64,
                'attachments'   : attachments
        })

        # pandas DataFrame으로 변환
        df = pd.DataFrame(data)

        return df


if __name__ == '__main__':
    import warnings

    # CUDA/MPS 경고 무시
    warnings.filterwarnings("ignore",
                            message="Neither CUDA nor MPS are available - defaulting to CPU. Note: This module is much faster with a GPU.")

    crawler = Crawl('login_id', 'login_pw')

    for board in crawler.table_names:
        print(board)
        df_post_detail = pd.DataFrame()
        df_post_target = pd.DataFrame()
        i = 74
        while True:
            try:
                targets = crawler.get_posts_urls(board, i)
                df_post_target = pd.concat([df_post_target, targets], ignore_index=True)
                if targets is None:
                    break
                print(targets)
                for link in targets['link']:
                    try:
                        df_post_detail = pd.concat([df_post_detail, crawler.get_post_details(link)], ignore_index=True)
                    except Exception as e:
                        print(e)
                        continue
                print(i)
                i += 1
            except Exception as e:
                print(e)
                continue
        df_posts = pd.concat([df_post_target, df_post_detail], axis=1).to_csv(f'{board}.csv')
        if df_posts is None:
            continue
        df_posts = df_posts.loc[:, ~df_posts.columns.duplicated()]
        df_posts.to_csv(f'{board}.csv')

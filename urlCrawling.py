import sys
import time
import os
import pandas as pd
from playwright.sync_api import sync_playwright, Page

def crawl_blog_ids(page: Page, keyword: str, start_page: int, end_page: int) -> list:
    """네이버 블로그에서 특정 키워드로 검색하여 블로그 ID를 크롤링합니다."""
    print(f"[{keyword}] 키워드로 블로그 ID 크롤링 시작... (페이지 {start_page} ~ {end_page})")
    id_url_list = []

    for i in range(start_page, end_page + 1): # start_page부터 end_page까지
        web_url = f"https://section.blog.naver.com/Search/Post.naver?pageNo={i}&rangeType=ALL&orderBy=sim&keyword={keyword}"
        print(f"  페이지 {i} 접속: {web_url}")
        try:
            page.goto(web_url, timeout=60000) # 60초로 타임아웃 증가
            page.wait_for_load_state("domcontentloaded", timeout=60000) # 로드 상태를 domcontentloaded로 변경 및 타임아웃 증가
            
            # 최소한 하나의 '.author' 요소가 페이지에 나타날 때까지 기다립니다.
            page.wait_for_selector('.author', timeout=10000) # 10초 대기
        except Exception as e:
            print(f"  [오류] 페이지 {i} 접속 또는 요소 대기 중 문제 발생: {e}")
            print("크롤링을 중단합니다.")
            sys.exit(1) # 오류 발생 시 비정상 종료

        # 'author' 클래스를 가진 모든 요소 (블로그 작성자 링크) 찾기
        author_elements = page.locator('.author').all()
        for author_element in author_elements:
            href = author_element.get_attribute('href')
            if href:
                id_url_list.append(href)
        time.sleep(1) # 과도한 요청 방지

    print(f"총 {len(id_url_list)}개의 블로그 URL 수집 완료.")
    
    # 링크에서 블로그 ID 추출 및 중복 제거
    id_list = [url.split('/')[3] for url in id_url_list if len(url.split('/')) > 3]
    current_id_list = list(set(id_list))
    print(f"현재 크롤링에서 중복 제거된 블로그 ID: {len(current_id_list)}개")
    
    # 이미 서이추한 블로그 ID 확인
    added_buddy_filename = f'addedBuddy.csv'
    try:
        existing_df = pd.read_csv(added_buddy_filename, header=None)
        print(f"이미 서이추한 블로그 ID {len(existing_df)}개 확인됨")
    except FileNotFoundError:
        print("이미 서이추한 블로그 ID 파일이 없습니다. addedBuddy.csv파일을 새로 생성합니다.")
        existing_df = pd.DataFrame(columns=[0])
    except Exception as e:
        existing_df = pd.DataFrame(columns=[0])

    # CSV 파일명 설정
    crawled_buddy_filename = f'naver_blogId_{keyword}.csv'
    try:
        existing_ids = set(existing_df[0].astype(str).tolist())
        print(f"이미 서이추한 블로그 ID {len(existing_ids)}개 확인됨")

        # 새로운 ID만 필터링 (기존 ID와 중복되지 않는 것만)
        new_ids = [id for id in current_id_list if id not in existing_ids]
        print(f"새로 추가될 ID: {len(new_ids)}개")

        # 새로운 ID가 있는 경우만 CSV에 저장
        if new_ids:
            try:
                df = pd.DataFrame(new_ids)
                df.to_csv(crawled_buddy_filename, mode='w', header=False, index=False)
            except Exception as e:
                print(f"블로그 ID CSV 저장 중 오류 발생: {e}")
                sys.exit(1)
        else:
            print("새로 추가할 ID가 없습니다.")
            sys.exit(1)
    except Exception as e:
        print(f"기존 파일 읽기 중 오류, 종료합니다. {e}")
        sys.exit(1)
    
def main_crawling():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        if len(sys.argv) < 2:
            print("키워드가 전달되지 않았습니다. 프로그램을 종료합니다.")
            sys.exit(1)
        KEYWORD = sys.argv[1].strip()
        if not KEYWORD:
            print("키워드가 입력되지 않았습니다. 프로그램을 종료합니다.")
            sys.exit(1)
            
        print(f"키워드: {KEYWORD}")
        
        start_page = int(input("\n시작 페이지를 입력하세요 (예: 1): ").strip())
        end_page = int(input("마지막 페이지를 입력하세요 (예: 5): ").strip())
        
        if start_page <= 0 or end_page <= 0:
            print("페이지 번호는 1 이상이어야 합니다. 프로그램을 종료합니다.")
            sys.exit(1)
        
        if start_page > end_page:
            print("시작 페이지가 마지막 페이지보다 클 수 없습니다. 프로그램을 종료합니다.")
            sys.exit(1)

        print(f"\n[{KEYWORD}] 키워드로 페이지 {start_page} ~ {end_page} 크롤링을 시작합니다...")
        try:
            crawl_blog_ids(page, KEYWORD, start_page, end_page)
        except Exception as e:
            print(f"크롤링 중 치명적인 오류 발생: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    main_crawling()

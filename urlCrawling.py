import sys
import time
import pandas as pd
from playwright.sync_api import sync_playwright, Page

def crawl_blog_ids(page: Page, keyword: str, repeat_pages: int) -> list:
    """네이버 블로그에서 특정 키워드로 검색하여 블로그 ID를 크롤링합니다."""
    print(f"[{keyword}] 키워드로 블로그 ID 크롤링 시작...")
    id_url_list = []

    for i in range(1, repeat_pages + 1): # pageNo는 1부터 시작
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
    final_id_list = list(set(id_list))
    print(f"최종 중복 제거된 블로그 ID: {len(final_id_list)}개")

    # CSV 파일로 저장
    try:
        df = pd.DataFrame(final_id_list)
        # 파일명을 키워드에 따라 동적으로 생성
        csv_filename = f'naver_blogId_{keyword}.csv'
        df.to_csv(csv_filename, mode='a', header=False, index=False)
        print(f"블로그 ID를 '{csv_filename}' 파일에 저장했습니다.")
    except Exception as e:
        print(f"블로그 ID CSV 저장 중 오류 발생: {e}")
        sys.exit(1) # CSV 저장 중 오류 발생 시 비정상 종료

    return final_id_list

def main_crawling():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        if len(sys.argv) < 2:
            print("키워드가 전달되지 않았습니다. 프로그램을 종료합니다.")
            sys.exit(1)
        KEYWORD = sys.argv[1].strip()
        if not KEYWORD:
            print("키워드가 입력되지 않았습니다. 프로그램을 종료합니다.")
            sys.exit(1) # 오류 종료
            
        REPEAT_PAGES = int(input("검색할 페이지 수를 입력하세요 (예: 2): ").strip())
        if REPEAT_PAGES <= 0:
            print("페이지 수는 1 이상이어야 합니다. 프로그램을 종료합니다.")
            sys.exit(1) # 오류 종료
        
        print(f"[{KEYWORD}] 키워드로 블로그 ID 크롤링 시작...")
        try:
            crawl_blog_ids(page, KEYWORD, REPEAT_PAGES)
        except Exception as e:
            print(f"크롤링 중 치명적인 오류 발생: {e}")
            sys.exit(1) # 치명적인 오류 발생 시 비정상 종료
        finally:
            browser.close()

if __name__ == "__main__":
    main_crawling()

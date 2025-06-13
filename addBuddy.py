import time
import pandas as pd
from playwright.sync_api import sync_playwright

# --- 사용자 설정 ---
# 서로이웃추가 시 보낼 메시지
MESSAGE_FOR_BUDDY = '안녕하세요, 게시물 잘 보았습니다. 자주소통하면서 서로이웃추가 요청드려요!' 
# --- 사용자 설정 끝 ---

def add_buddy_to_blogs(page, blog_ids: list, message: str):
    """크롤링된 블로그 ID 목록을 순회하며 서로이웃추가를 시도합니다."""
    print("서로이웃추가 시작...")
    clicked_count = 0
    
    for blog_id in blog_ids:
        try:
            print(f"  블로그 ID: {blog_id} 에 서로이웃추가 시도 중...")
            blog_url = f'https://m.blog.naver.com/BuddyAddForm.naver?blogId={blog_id}'
            page.goto(blog_url)
            page.wait_for_load_state("domcontentloaded") # 빠른 로드 대기

            # '서이추 기능이 disable일 시 다음 id로 넘김' 로직 번역
            exceptional_text_element = page.locator('.dsc').first
            exceptional_text = exceptional_text_element.text_content() if exceptional_text_element.count() > 0 else ""

            # 'bothBuddyRadio' 버튼의 활성화 여부 확인
            both_buddy_radio = page.locator('#bothBuddyRadio')
            is_both_buddy_radio_enabled = both_buddy_radio.is_enabled()

            # 조건 검사 (원래 Selenium 코드의 로직 번역)
            conditions_met = (
                is_both_buddy_radio_enabled and
                "제한된" not in exceptional_text and
                "진행중" not in exceptional_text and
                '하루에' not in exceptional_text
            )
            
            if conditions_met:
                both_buddy_radio.click()
                time.sleep(1) # 클릭 후 잠시 대기

                # 미리 입력된 기본값을 지우고 메시지 입력
                textarea = page.locator('textarea')
                textarea.fill(message)
                time.sleep(1)

                # 확인 버튼 누르기
                page.locator('.btn_ok').click()
                page.wait_for_load_state("networkidle") # 버튼 클릭 후 페이지 변화 대기
                print(f"    [{blog_id}] 서로이웃추가 요청 완료.")
                clicked_count += 1
            else:
                print(f"    [{blog_id}] 서로이웃추가 불가 (조건 미충족 또는 이미 이웃): {exceptional_text}")

            time.sleep(1) # 다음 블로그 이동 전 충분히 대기

        except Exception as e:
            print(f"    [{blog_id}] 서로이웃추가 중 오류 발생: {e}")

            if(e in 'Target page, context or browser has been closed'):
                break;
            
            time.sleep(2) # 오류 발생 시 더 길게 대기
            pass # 다음 ID로 진행

    print(f"총 {clicked_count}개의 서로이웃추가 요청을 보냈습니다.")

def main():
    import sys
    # 배치파일에서 전달받은 키워드 사용
    if len(sys.argv) < 2:
        print("키워드가 전달되지 않았습니다. 프로그램을 종료합니다.")
        return
    keyword_for_csv = sys.argv[1].strip()
    if not keyword_for_csv:
        print("키워드가 입력되지 않았습니다. 프로그램을 종료합니다.")
        return

    csv_filename = f'naver_blogId_{keyword_for_csv}.csv'

    # CSV 파일에서 블로그 ID 읽어오기
    try:
        df = pd.read_csv(csv_filename, header=None)
        blog_ids_from_csv = df[0].tolist()
        print(f"'{csv_filename}' 파일에서 {len(blog_ids_from_csv)}개의 블로그 ID를 읽었습니다.")
    except FileNotFoundError:
        print(f"오류: 파일 '{csv_filename}'을 찾을 수 없습니다. 먼저 urlCrawling.py를 실행하여 CSV 파일을 생성하세요.")
        return
    except Exception as e:
        print(f"CSV 파일 읽기 중 오류 발생: {e}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # 테스트 시엔 False, 실제 사용 시 True (기본값)
        page = browser.new_page()

        try:
            if blog_ids_from_csv:
                add_buddy_to_blogs(page, blog_ids_from_csv, MESSAGE_FOR_BUDDY)
            else:
                print("CSV 파일에 블로그 ID가 없어 서로이웃추가를 진행하지 않습니다.")

        except Exception as e:
            print(f"메인 스크립트 실행 중 치명적인 오류 발생: {e}")

        finally:
            print("브라우저를 닫습니다.")
            browser.close()

if __name__ == "__main__":
    main()


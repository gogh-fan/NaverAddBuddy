chcp 65001

if not exist venv (
    echo 가상 환경 "venv"를 생성합니다...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
playwright install

set /p keyword="검색할 키워드를 입력하세요: "
python.exe urlCrawling.py "%keyword%"
rem urlCrawling.py 실행 결과 확인
if %ERRORLEVEL% NEQ 0 (
    echo urlCrawling.py 실행 중 오류가 발생했습니다. addBuddy.py를 실행하지 않고 종료합니다.
) else (
    echo urlCrawling.py가 성공적으로 실행되었습니다. addBuddy.py를 실행합니다.
    python.exe addBuddy.py "%keyword%"
)
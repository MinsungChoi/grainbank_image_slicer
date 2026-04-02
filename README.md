# Image Slicer Project

상세페이지와 같이 세로로 긴 이미지를 논리적 구간별로 자동 분할하는 프로그램입니다.

## 주요 기능
- **자동 공백 감지**: 이미지 내의 단색 가로선(Gap)을 분석하여 절단 지점을 자동으로 결정합니다.
- **배경색 적응형 로직**: `numpy`의 분산(Variance) 분석을 통해 미세한 색상 차이가 있는 배경도 공백으로 인식할 수 있습니다.
- **최소 높이 설정**: 너무 작게 쪼개지는 것을 방지하여 최적의 슬라이스 크기를 유지합니다.

## 디렉토리 구조
- `src/`: 핵심 소스 코드 (`slicer.py`)
- `img/`: 입력 및 출력 이미지 저장소 (`img/output/`에 결과물 저장)
- `docs/`: 프로젝트 명세 및 기술 문서

## 🚀 Streamlit 웹 대시보드 (그레인뱅크 전용)
로컬 환경뿐만 아니라 **Streamlit Cloud**에 배포하여 웹 브라우저에서 바로 사용할 수 있는 대시보드 기능을 제공합니다.

### 실행 방법 (로컬)
```bash
streamlit run src/app.py
```

### Streamlit 배포 시 필수 파일 (Git 업로드 항목)
1.  **`src/app.py`**: 웹 대시보드 인터페이스 코드
2.  **`src/slicer.py`**: 이미지 분석 로직 (app.py에서 참조)
3.  **`requirements.txt`**: 의존성 라이브러리 목록 (`streamlit`, `pillow`, `numpy`)
4.  **`README.md`**: 프로젝트 설명

### 배포 절차 (Streamlit Cloud 기준)
1.  GitHub 저장소에 위 파일들을 업로드합니다.
2.  [Streamlit Cloud](https://share.streamlit.io/)에 로그인 후 **"New app"**을 클릭합니다.
3.  저장소를 선택하고 `Main file path`를 `src/app.py`로 설정하여 배포합니다.

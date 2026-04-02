import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import io
import zipfile
import os

def slice_image_in_memory(image_file, min_gap_height=10, variance_threshold=1.0, min_slice_height=500, manual_points=None):
    """
    Slices an image in memory and returns a list of (filename, bytes) tuples.
    """
    # Load image
    img = Image.open(image_file).convert('RGB')
    width, height = img.size
    img_array = np.array(img)

    if manual_points is None:
        # Calculate variance for each row
        row_variances = np.var(img_array, axis=(1, 2))
        
        # Identify "gap" rows
        is_gap_row = row_variances <= variance_threshold
        
        # Find contiguous blocks of gap rows
        gap_points = []
        current_gap_start = -1
        
        for y in range(height):
            if is_gap_row[y]:
                if current_gap_start == -1:
                    current_gap_start = y
            else:
                if current_gap_start != -1:
                    gap_height = y - current_gap_start
                    if gap_height >= min_gap_height:
                        gap_points.append(current_gap_start + gap_height // 2)
                    current_gap_start = -1
        
        # Final slice points
        slice_indices = [0]
        last_slice_y = 0
        for gap_y in gap_points:
            if gap_y - last_slice_y >= min_slice_height:
                slice_indices.append(gap_y)
                last_slice_y = gap_y
        slice_indices.append(height)
    else:
        # Use manual points (sorted and within bounds)
        valid_points = sorted([p for p in manual_points if 0 < p < height])
        slice_indices = [0] + valid_points + [height]
    
    slices = []
    for i in range(len(slice_indices) - 1):
        top = slice_indices[i]
        bottom = slice_indices[i+1]
        if top >= bottom: continue
        
        slice_img = img.crop((0, top, width, bottom))
        
        # Save to buffer
        buf = io.BytesIO()
        slice_img.save(buf, format="PNG")
        slices.append((f"slice_{i+1:02d}.png", buf.getvalue()))
        
    return slices, slice_indices

# --- Streamlit UI ---
st.set_page_config(page_title="그레인뱅크 상세페이지 슬라이서", layout="wide")

# Session State for Manual Coordinates
if 'manual_coords' not in st.session_state:
    st.session_state.manual_coords = ""

st.title("🍉 그레인뱅크 상세페이지 이미지 슬라이서")
st.markdown("""
상세페이지 이미지를 업로드하면 자동으로 섹션별로 분할해줍니다. 
자동 감지된 절단선을 기반으로 수동으로 정교하게 수정할 수 있습니다.
""")

with st.sidebar:
    st.header("⚙️ 설정")
    mode = st.radio("모드 선택", ["자동 감지", "수동 입력"])
    
    gap_h = 10
    var_t = 1.0
    min_h = 500

    if mode == "자동 감지":
        gap_h = st.slider("최소 구분선 두께 (px)", 1, 50, 10)
        var_t = st.slider("배경 감지 감도 (Variance)", 0.0, 10.0, 1.0, 0.1)
        min_h = st.slider("최소 슬라이스 높이 (px)", 100, 2000, 500)
        st.divider()
        st.info("자동으로 감지된 선을 수정하고 싶다면 아래 버튼을 눌러 '수동 입력' 모드로 전환하세요.")
    else:
        st.info("절단할 Y 좌표를 쉼표(,)나 엔터로 구분해서 입력하세요.")
        st.session_state.manual_coords = st.text_area("수동 절단 좌표 (Y)", value=st.session_state.manual_coords, placeholder="예: 1200, 2500, 4800", height=200)

uploaded_file = st.file_uploader("상세페이지 이미지를 선택하세요 (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file:
    import plotly.express as px
    import plotly.graph_objects as go

    # Initial pass for Auto Detection to show in UI and support copying
    auto_slices, auto_indices = slice_image_in_memory(uploaded_file, gap_h, var_t, min_h, manual_points=None)
    auto_coords_str = ", ".join(map(str, auto_indices[1:-1]))

    # If in Auto mode, provide a button to copy to manual
    if mode == "자동 감지":
        if st.sidebar.button("📋 자동 좌표를 수동으로 복사"):
            st.session_state.manual_coords = auto_coords_str
            st.sidebar.success("좌표가 복사되었습니다! '수동 입력' 모드로 전환하여 수정하세요.")

    # Parse Manual Points if in Manual mode
    manual_points = None
    if mode == "수동 입력" and st.session_state.manual_coords:
        try:
            import re
            manual_points = [int(p.strip()) for p in re.split(r'[,\n\s]+', st.session_state.manual_coords) if p.strip().isdigit()]
        except ValueError:
            st.error("좌표 입력 형식이 올바르지 않습니다.")

    with st.sidebar:
        st.divider()
        st.header("🖼️ 시스템 설정")
        preview_h = st.slider("미리보기 세로 길이 (px)", 400, 2000, 800)

    # Process Final Slices
    slices, indices = slice_image_in_memory(uploaded_file, gap_h, var_t, min_h, manual_points=manual_points)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("💡 인터랙티브 미리보기 (Y좌표 확인)")
        st.info("마우스를 올리면 Y좌표가 표시됩니다. 확대/이동 도구 모음은 우측 상단에 있습니다.")
        
        img_preview = Image.open(uploaded_file).convert('RGB')
        
        # Use Plotly for interactive preview
        fig = px.imshow(img_preview, binary_string=True)
        
        # Color line based on mode
        line_color = "red" if mode == "자동 감지" else "lime"
        
        # Add slice lines as hlines in Plotly
        for y in indices[1:-1]:
            fig.add_hline(y=y, line_width=2, line_dash="dash", line_color=line_color)
            
        fig.update_layout(
            height=preview_h, # Apply user-defined height
            margin=dict(l=0, r=0, t=0, b=0),
            dragmode='pan',
            hovermode='closest',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )
        
        # Update hover template to focus on Y coordinate
        fig.update_traces(
            hovertemplate="Y: %{y}<extra></extra>"
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        
        st.success(f"총 {len(slices)}개의 조각으로 분리되었습니다.")
        
        st.write(f"{mode} 결과 좌표:")
        st.code(", ".join(map(str, indices[1:-1])))

    with col2:
        st.subheader("결과 다운로드")
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for filename, data in slices:
                zf.writestr(filename, data)
        
        st.download_button(
            label="📦 모든 조각 ZIP으로 다운로드",
            data=zip_buffer.getvalue(),
            file_name=f"slices_{uploaded_file.name}.zip",
            mime="application/zip",
            use_container_width=True
        )
        
        st.divider()
        st.write("조각별 미리보기 (일부):")
        for filename, data in slices[:15]:
            st.image(data, caption=filename, width=400)
        if len(slices) > 15:
            st.write(f"...외 {len(slices)-15}개 조각")

else:
    st.info("이미지 파일을 업로드하면 분석이 시작됩니다.")

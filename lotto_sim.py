import streamlit as st
import random
import time
import datetime
import pandas as pd
import os
import base64

# 페이지 설정
st.set_page_config(page_title="Cafe Lucky Event", page_icon="🎰", layout="centered")

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "lotto_history.txt")
BACKGROUND_IMG = os.path.join(BASE_DIR, "background.png")
BOUNCE_SOUND = os.path.join(BASE_DIR, "bounce.wav")

# 파일이 없을 경우를 대비한 기본 설정
if not os.path.exists(HISTORY_FILE):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        pass

@st.cache_data
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def get_ball_color(n):
    """번호에 따른 로또 공 색상을 반환합니다."""
    if n <= 10: return "#fbc400"  # 노란색
    if n <= 20: return "#69c8f2"  # 파란색
    if n <= 30: return "#ff7272"  # 빨간색
    if n <= 40: return "#aaaaaa"  # 회색
    return "#b0d840"              # 초록색

def load_history_from_file():
    """파일에서 추첨 이력을 읽어옵니다. (배포 환경의 실시간 반영을 위해 캐싱 제거)"""
    history = []
    if os.path.exists(HISTORY_FILE) and os.path.getsize(HISTORY_FILE) > 0:
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line and "]" in line:
                        t, r = line.split("]", 1)
                        history.append({"시간": t[1:].strip(), "결과": r.strip()})
        except Exception as e:
            st.error(f"이력 로드 중 오류 발생: {e}")
    return history

@st.cache_data
def get_base64_audio(file_path):
    """사운드 파일을 Base64로 인코딩하여 캐싱합니다."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def play_sound(file_path, placeholder):
    """사운드 재생을 위한 HTML 삽입 (플레이스홀더를 사용하여 DOM 비대화 방지)"""
    b64 = get_base64_audio(file_path)
    if b64:
        audio_html = f'<audio autoplay key="{time.time()}"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>'
        placeholder.markdown(audio_html, unsafe_allow_html=True)

# 스타일 설정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    }

    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #FF4B4B; color: white; }
    
    .machine-wrapper {
        position: relative; width: 100%; max-width: 700px; margin: 0 auto;
        aspect-ratio: 16 / 9; background-color: #050505;
        border-radius: 30px; border: 4px solid #333;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        overflow: hidden;
        isolation: isolate;
    }
    .pile-container {
        position: absolute; top: 45%; left: 50%; transform: translate(-50%, -50%);
        width: 250px; height: 180px;
        perspective: 500px;
    }
    /* 회전하는 투명 날개 설정 */
    .wings-container {
        position: absolute; top: 45%; left: 50%; width: 220px; height: 160px;
        transform: translate(-50%, -50%); z-index: 0; pointer-events: none;
    }
    .wing {
        position: absolute; top: 50%; left: 50%; width: 130px; height: 2px;
        background: rgba(255, 255, 255, 0.1);
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.05);
        transform-origin: center center;
    }
    .wing-1 { transform: translate(-50%, -50%) rotate(0deg); }
    .wing-2 { transform: translate(-50%, -50%) rotate(120deg); }
    .wing-3 { transform: translate(-50%, -50%) rotate(240deg); }

    .shuffling-machine .wings-container {
        animation: rotateWings 0.6s linear infinite;
    }

    @keyframes rotateWings {
        from { transform: translate(-50%, -50%) rotate(0deg); }
        to { transform: translate(-50%, -50%) rotate(360deg); }
    }

    .ball {
        position: absolute; width: 34px; height: 34px; border-radius: 50%;
        display: flex; justify-content: center; align-items: center;
        color: white; font-weight: 900; font-size: 13px;
        box-shadow: inset -4px -4px 6px rgba(0,0,0,0.4), 2px 2px 4px rgba(0,0,0,0.3);
        border: 1px solid rgba(0,0,0,0.1);
        transition: none; /* Python에 의한 강제 위치 이동 시 부드럽게 연결 */
        /* 텍스트 깨짐 방지 핵심 설정 */
        isolation: isolate; 
        backface-visibility: hidden;
        transform: translateZ(0);
        -webkit-transform: translateZ(0);
        -webkit-font-smoothing: antialiased;
    }
    .ball::after {
        content: ''; position: absolute; width: 70%; height: 70%;
        background: rgba(255, 255, 255, 1.0); border-radius: 50%;
        z-index: 0; top: 50%; left: 50%; transform: translate(-50%, -50%);
    }
    .ball-text { 
        position: relative; z-index: 2; color: black; font-weight: 900; 
        line-height: 1; pointer-events: none;
    }
    .exit-port {
        position: absolute; bottom: 5%; left: 50%; transform: translateX(-50%);
        display: flex; gap: 10px; justify-content: center; width: 100%;
    }
    .drawn-ball { 
        width: 48px; height: 48px; font-size: 18px; position: relative; 
        animation: ballPop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    /* 공별 무규칙 움직임을 위한 애니메이션 */
    .shuffling-ball { 
        animation: ballChaos var(--dur) ease-in-out var(--delay) infinite alternate;
    }
    
    @keyframes ballPop {
        0% { transform: scale(0) translateY(20px); opacity: 0; }
        100% { transform: scale(1) translateY(0); opacity: 1; }
    }
    
    @keyframes ballChaos {
        0% { transform: translate(0, 0); }
        100% { transform: translate(var(--mx), var(--my)); }
    }
    </style>
    """, unsafe_allow_html=True)

def render_machine(balls_to_show, drawn_ones=[], shuffle=False):
    shuffle_class = "shuffling-machine" if shuffle else ""
    html = f'<div class="machine-wrapper {shuffle_class}">'
    
    # 투명 날개 추가
    html += '''<div class="wings-container">
        <div class="wing wing-1"></div>
        <div class="wing wing-2"></div>
        <div class="wing wing-3"></div>
    </div>'''
    
    html += '<div class="pile-container">'
    for i, n in enumerate(balls_to_show):
        # 전역 random.seed 대신 로컬 Random 인스턴스를 사용하여 추첨 결과가 매번 똑같이 나오는 문제 해결
        pos_rng = random.Random(n + 777)
        base_top = pos_rng.randint(5, 75)
        base_left = pos_rng.randint(5, 75)
        
        # 셔플 중일 때 공마다 다른 속도와 방향 부여
        shuffle_style = ""
        if shuffle:
            # time.time() 시드 제거로 애니메이션 끊김 현상 해결
            dur = random.uniform(0.06, 0.12)
            delay = random.uniform(0, 0.1)
            mx, my = random.randint(-70, 70), random.randint(-70, 70)
            shuffle_style = f'--dur:{dur}s; --delay:{delay}s; --mx:{mx}px; --my:{my}px;'
        
        color = get_ball_color(n)
        html += f'<div class="ball {"shuffling-ball" if shuffle else ""}" style="background-color: {color}; top: {base_top}%; left: {base_left}%; z-index: {i+1}; {shuffle_style}"><span class="ball-text">{n}</span></div>'
    html += '</div><div class="exit-port">'
    for n in drawn_ones:
        color = get_ball_color(n)
        html += f'<div class="ball drawn-ball" style="background-color: {color}; position: static; display: flex;"><span class="ball-text">{n}</span></div>'
    return html + '</div></div>'

def main():
    # UI 플레이스홀더를 실행 함수 내부에서 생성하여 컨텍스트 경고 방지
    machine_placeholder = st.empty()
    sound_placeholder = st.empty()

    img_base64 = get_base64_image(BACKGROUND_IMG)
    
    # 스타일을 동적으로 생성하여 클래스에 직접 적용 (CSS 변수보다 호환성 높음)
    if img_base64:
        st.markdown(f"""
            <style type="text/css">
            .stApp .machine-wrapper {{
                background-image: url('data:image/png;base64,{img_base64}');
                background-size: cover; background-repeat: no-repeat; background-position: center;
            }}
            </style>""", unsafe_allow_html=True)

    with st.sidebar:
        st.title("⚙️ 추첨 설정")
        
        # 제외수 선택 기능 추가
        exclude_nums = st.multiselect("🚫 제외할 번호 (제외수)", list(range(1, 46)), help="여기에 선택한 번호는 추첨기에서 제외됩니다.")
        
        # 고정수 선택 기능 추가
        fixed_nums = st.multiselect("📌 고정할 번호 (고정수)", [n for n in range(1, 46) if n not in exclude_nums], help="결과에 반드시 포함될 번호입니다.")

        # 제외수를 제외한 나머지 번호들 계산
        available_pool = [n for n in range(1, 46) if n not in exclude_nums]
        
        selected_nums = st.multiselect("✅ 추첨기에 넣을 번호 (최종)", available_pool, default=available_pool)
        
        # 추첨 가능한 번호 개수 계산
        pool_size = len(selected_nums)
        
        if pool_size > 0:
            # 뽑을 개수가 고정수 개수보다 작지 않도록 제한
            target_count = st.number_input("뽑을 공의 개수", min_value=max(1, len(fixed_nums)), max_value=pool_size, value=max(min(6, pool_size), len(fixed_nums)))
        else:
            st.warning("⚠️ 추첨기에 공이 없습니다. 제외수를 줄여주세요.")
            target_count = 0
        
        if st.button("🗑️ 전체 기록 삭제", type="secondary"):
            if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
            st.session_state.history = []
            st.rerun()

        st.divider()
        with st.expander("📝 수동 결과 직접 입력"):
            manual_input = st.text_input("번호 입력 (쉼표 구분)", placeholder="18, 19, 20, 43, 44, 45")
            if st.button("기록에 추가"):
                try:
                    # 입력받은 문자열을 숫자로 변환하고 중복 제거 및 정렬
                    raw_nums = [int(n.strip()) for n in manual_input.split(",") if n.strip()]
                    nums = sorted(list(set(raw_nums)))
                    
                    if len(nums) != len(raw_nums):
                        st.warning("⚠️ 중복된 번호는 자동으로 제거되었습니다.")
                    
                    # 1개 이상 45개 이하의 숫자가 입력되었는지 확인 (유연성 확보)
                    if 1 <= len(nums) <= 45:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        res_str = ", ".join(map(str, nums))
                        try:
                            # 파일에 저장
                            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                                f.write(f"[{now}] {res_str}\n")
                            st.cache_data.clear() # 관련 캐시 초기화
                        except Exception as e:
                            st.error(f"기록 저장 실패: {e}")
                            
                        # 현재 세션에도 반영
                        st.session_state.history.append({"시간": now, "결과": res_str})
                        st.success("결과가 성공적으로 저장되었습니다!")
                        st.rerun()
                    else:
                        st.error("1개에서 45개 사이의 숫자를 입력해야 합니다.")
                except ValueError:
                    st.error("올바른 숫자 형식이 아닙니다 (예: 1, 2, 3, 4, 5, 6)")

    if 'drawn_result' not in st.session_state: st.session_state.drawn_result = []
    if 'history' not in st.session_state:
        st.session_state.history = load_history_from_file()

    remaining_balls = [n for n in selected_nums if n not in st.session_state.drawn_result]
    machine_placeholder.markdown(render_machine(remaining_balls, st.session_state.drawn_result), unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1: start_btn = st.button("🎰 행운의 번호 추첨 시작!", type="primary")
    with c2: 
        if st.button("🔄 화면 초기화"):
            st.session_state.drawn_result = []
            st.rerun()

    if start_btn:
        if target_count == 0:
            st.error("⚠️ 추첨할 공이 없습니다.")
        elif not all(num in selected_nums for num in fixed_nums):
            st.error("⚠️ 고정수가 '추첨기에 넣을 번호'에 포함되어야 합니다.")
        elif len(selected_nums) < target_count:
            st.error("⚠️ 추첨할 공이 부족합니다. 제외수를 확인하거나 번호를 더 선택해주세요.")
        else:
            st.session_state.drawn_result = []
            temp_nums = list(selected_nums)
            
            # 고정수를 포함한 당첨 번호 미리 선정
            pool_for_random = [n for n in selected_nums if n not in fixed_nums]
            winners = fixed_nums + random.sample(pool_for_random, int(target_count) - len(fixed_nums))
            random.shuffle(winners) # 고정수와 일반수가 섞여서 나오도록 셔플
            
            with st.status("🔮 기계가 작동 중입니다. 잠시만 기다려 주세요...", expanded=False) as status:
                for i in range(int(target_count)):
                    # 셔플 횟수를 늘려 공이 충분히 섞이는 느낌을 줌 (4회 -> 10회)
                    for _ in range(10):
                        machine_placeholder.markdown(render_machine(temp_nums, st.session_state.drawn_result, True), unsafe_allow_html=True)
                        time.sleep(0.1)
                    
                    pick = winners[i]
                    temp_nums.remove(pick)
                    st.session_state.drawn_result.append(pick)
                    
                    # 사운드 재생
                    play_sound(BOUNCE_SOUND, sound_placeholder)
                    
                    machine_placeholder.markdown(render_machine(temp_nums, st.session_state.drawn_result), unsafe_allow_html=True)
                    
                    # 각 번호가 나올 때 사용자가 번호를 인지할 수 있도록 여유 시간 부여
                    if i == int(target_count) - 1:
                        time.sleep(2.0) # 마지막 공은 긴장감을 위해 더 오래 대기
                    else:
                        time.sleep(1.2) # 일반 공 대기 시간 연장 (0.6s -> 1.2s)

                status.update(label="✅ 추첨 완료!", state="complete")
            
            # 모든 결과가 화면에 완전히 그려진 후 풍선이 터지도록 충분한 여유 부여
            time.sleep(0.8)
            st.balloons()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            res_str = ", ".join(map(str, sorted(st.session_state.drawn_result)))
            st.session_state.history.append({"시간": now, "결과": res_str})
            
            try:
                with open(HISTORY_FILE, "a", encoding="utf-8") as f: f.write(f"[{now}] {res_str}\n")
            except Exception as e:
                st.error(f"파일 기록 중 오류 발생: {e}")
            st.toast(f"축하합니다! 추첨 번호: {res_str}")

    st.divider()
    
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        
        tab1, tab2 = st.tabs(["📋 추첨 기록", "📊 번호별 통계"])
        
        with tab1:
            st.dataframe(df.iloc[::-1], width="stretch", hide_index=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 전체 이력 다운로드 (CSV)",
                data=csv,
                file_name=f"lotto_history_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        with tab2:
            # 모든 결과 숫자를 분리하여 빈도 계산
            all_nums_flat = []
            for res in df["결과"]:
                all_nums_flat.extend([int(n.strip()) for n in res.split(",")])
            
            if all_nums_flat:
                counts = pd.Series(all_nums_flat).value_counts().sort_index()
                st.bar_chart(counts)
                st.caption("※ 현재까지 진행된 추첨 이력을 바탕으로 집계된 번호별 출현 횟수입니다.")
    else:
        st.info("아직 추첨 기록이 없습니다. 첫 번째 행운의 주인공이 되어보세요!")

if __name__ == "__main__":
    main()
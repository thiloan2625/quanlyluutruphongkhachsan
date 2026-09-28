import streamlit as st
import sqlite3
from datetime import datetime, date
from pathlib import Path
import pandas as pd

# ============================================================
# CẤU HÌNH
# ============================================================

st.set_page_config(
    page_title="Hotel Manager - Quản lý khách sạn",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = Path("hotel_manager.db")

ROOM_STATUSES = [
    "Trống",
    "Đã đặt",
    "Đang ở",
    "Đang dọn",
    "Bảo trì",
]

ROOM_TYPES = [
    "Standard",
    "Superior",
    "Deluxe",
    "Suite",
    "Family",
    "VIP",
]

STATUS_COLORS = {
    "Trống": "#22c55e",
    "Đã đặt": "#3b82f6",
    "Đang ở": "#f59e0b",
    "Đang dọn": "#8b5cf6",
    "Bảo trì": "#ef4444",
}


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            floor INTEGER NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Trống',
            guest_name TEXT DEFAULT '',
            guest_phone TEXT DEFAULT '',
            check_in TEXT DEFAULT '',
            check_out TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL,
            guest_name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            adults INTEGER DEFAULT 1,
            children INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Đã đặt',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            room_number TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Tạo dữ liệu phòng mẫu nếu database chưa có phòng
    count = cursor.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]

    if count == 0:
        sample_rooms = []

        # 15 phòng mẫu: 101-105, 201-205, 301-305
        for floor in [1, 2, 3]:
            for number in range(1, 6):
                room_number = f"{floor}{number:02d}"

                if number == 1 and floor == 1:
                    status = "Đang ở"
                    guest = "Nguyễn Văn An"
                    phone = "0901234567"
                    check_in = date.today().isoformat()
                    check_out = date.today().isoformat()
                elif number == 2 and floor == 1:
                    status = "Đã đặt"
                    guest = "Trần Thị Mai"
                    phone = "0912345678"
                    check_in = ""
                    check_out = ""
                elif number == 3 and floor == 2:
                    status = "Đang dọn"
                    guest = ""
                    phone = ""
                    check_in = ""
                    check_out = ""
                elif number == 4 and floor == 3:
                    status = "Bảo trì"
                    guest = ""
                    phone = ""
                    check_in = ""
                    check_out = ""
                else:
                    status = "Trống"
                    guest = ""
                    phone = ""
                    check_in = ""
                    check_out = ""

                room_type = ["Standard", "Superior", "Deluxe", "Suite", "Family"][number - 1]
                price = {
                    "Standard": 800000,
                    "Superior": 1100000,
                    "Deluxe": 1500000,
                    "Suite": 2200000,
                    "Family": 2800000,
                }[room_type]

                sample_rooms.append(
                    (
                        room_number,
                        floor,
                        room_type,
                        price,
                        status,
                        guest,
                        phone,
                        check_in,
                        check_out,
                        "",
                    )
                )

        cursor.executemany("""
            INSERT INTO rooms
            (
                room_number, floor, room_type, price, status,
                guest_name, guest_phone, check_in, check_out, note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_rooms)

        conn.commit()

    conn.close()


def log_activity(action, room_number="", description=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO activity_logs
        (action, room_number, description)
        VALUES (?, ?, ?)
    """, (action, room_number, description))
    conn.commit()
    conn.close()


def get_rooms():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM rooms ORDER BY floor, room_number",
        conn
    )
    conn.close()
    return df


def get_room(room_number):
    conn = get_connection()
    room = conn.execute(
        "SELECT * FROM rooms WHERE room_number = ?",
        (room_number,)
    ).fetchone()
    conn.close()
    return room


def update_room_status(room_number, status):
    conn = get_connection()
    conn.execute(
        "UPDATE rooms SET status = ? WHERE room_number = ?",
        (status, room_number)
    )
    conn.commit()
    conn.close()

    log_activity(
        "Cập nhật trạng thái",
        room_number,
        f"Phòng chuyển sang trạng thái: {status}"
    )


def check_in_guest(
    room_number,
    guest_name,
    phone,
    check_in,
    check_out,
    note=""
):
    conn = get_connection()

    conn.execute("""
        UPDATE rooms
        SET
            status = 'Đang ở',
            guest_name = ?,
            guest_phone = ?,
            check_in = ?,
            check_out = ?,
            note = ?
        WHERE room_number = ?
    """, (
        guest_name,
        phone,
        check_in,
        check_out,
        note,
        room_number
    ))

    conn.commit()
    conn.close()

    log_activity(
        "Check-in",
        room_number,
        f"Khách: {guest_name}, SĐT: {phone}"
    )


def check_out_guest(room_number):
    room = get_room(room_number)

    if room is None:
        return

    guest_name = room["guest_name"]

    conn = get_connection()

    conn.execute("""
        UPDATE rooms
        SET
            status = 'Đang dọn',
            guest_name = '',
            guest_phone = '',
            check_in = '',
            check_out = ''
        WHERE room_number = ?
    """, (room_number,))

    conn.commit()
    conn.close()

    log_activity(
        "Check-out",
        room_number,
        f"Khách trả phòng: {guest_name}"
    )


def add_room(
    room_number,
    floor,
    room_type,
    price,
    status,
    note
):
    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO rooms
            (
                room_number, floor, room_type,
                price, status, note
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            room_number,
            floor,
            room_type,
            price,
            status,
            note
        ))

        conn.commit()
        success = True

    except sqlite3.IntegrityError:
        success = False

    conn.close()

    if success:
        log_activity(
            "Thêm phòng",
            room_number,
            f"Loại phòng: {room_type}"
        )

    return success


def update_room(
    room_id,
    room_number,
    floor,
    room_type,
    price,
    status,
    note
):
    conn = get_connection()

    try:
        conn.execute("""
            UPDATE rooms
            SET
                room_number = ?,
                floor = ?,
                room_type = ?,
                price = ?,
                status = ?,
                note = ?
            WHERE id = ?
        """, (
            room_number,
            floor,
            room_type,
            price,
            status,
            note,
            room_id
        ))

        conn.commit()
        success = True

    except sqlite3.IntegrityError:
        success = False

    conn.close()

    if success:
        log_activity(
            "Chỉnh sửa phòng",
            room_number,
            "Cập nhật thông tin phòng"
        )

    return success


def delete_room(room_id, room_number):
    conn = get_connection()
    conn.execute(
        "DELETE FROM rooms WHERE id = ?",
        (room_id,)
    )
    conn.commit()
    conn.close()

    log_activity(
        "Xóa phòng",
        room_number,
        "Phòng đã được xóa khỏi hệ thống"
    )


def add_booking(
    room_number,
    guest_name,
    phone,
    check_in,
    check_out,
    adults,
    children,
    note
):
    conn = get_connection()

    conn.execute("""
        INSERT INTO bookings
        (
            room_number, guest_name, phone,
            check_in, check_out,
            adults, children, status, note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Đã đặt', ?)
    """, (
        room_number,
        guest_name,
        phone,
        check_in,
        check_out,
        adults,
        children,
        note
    ))

    # Cập nhật trạng thái phòng
    conn.execute("""
        UPDATE rooms
        SET
            status = 'Đã đặt',
            guest_name = ?,
            guest_phone = ?,
            check_in = ?,
            check_out = ?
        WHERE room_number = ?
    """, (
        guest_name,
        phone,
        check_in,
        check_out,
        room_number
    ))

    conn.commit()
    conn.close()

    log_activity(
        "Tạo đặt phòng",
        room_number,
        f"Khách: {guest_name}"
    )


def get_bookings():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT *
        FROM bookings
        ORDER BY check_in ASC, id DESC
    """, conn)
    conn.close()
    return df


def get_logs():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT *
        FROM activity_logs
        ORDER BY id DESC
        LIMIT 100
    """, conn)
    conn.close()
    return df


# ============================================================
# CSS
# ============================================================

def load_css():
    st.markdown("""
    <style>

    .main {
        background-color: #f7f8fa;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    .hotel-title {
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 3px;
    }

    .hotel-subtitle {
        color: #6b7280;
        margin-bottom: 25px;
    }

    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        min-height: 120px;
    }

    .metric-title {
        color: #6b7280;
        font-size: 14px;
    }

    .metric-number {
        font-size: 30px;
        font-weight: 800;
        margin-top: 8px;
    }

    .room-card {
        background: white;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
        border: 1px solid #e5e7eb;
    }

    .room-number {
        font-size: 23px;
        font-weight: 800;
    }

    .guest-name {
        color: #374151;
        font-size: 14px;
        margin-top: 5px;
    }

    .status-badge {
        padding: 5px 10px;
        border-radius: 20px;
        color: white;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }

    .section-title {
        font-size: 21px;
        font-weight: 750;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    </style>
    """, unsafe_allow_html=True)


# ============================================================
# COMPONENTS
# ============================================================

def status_badge(status):
    color = STATUS_COLORS.get(status, "#6b7280")

    return f"""
    <span class="status-badge"
          style="background-color:{color};">
        {status}
    </span>
    """


def metric_card(title, number, description=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-number">{number}</div>
            <div style="color:#9ca3af;font-size:12px;">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def format_money(value):
    return f"{value:,.0f} VNĐ".replace(",", ".")


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():
    st.markdown(
        '<div class="hotel-title">🏨 Hotel Manager</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="hotel-subtitle">'
        'Hệ thống quản lý phòng khách sạn'
        '</div>',
        unsafe_allow_html=True
    )

    rooms = get_rooms()

    total = len(rooms)
    empty = len(rooms[rooms["status"] == "Trống"])
    booked = len(rooms[rooms["status"] == "Đã đặt"])
    occupied = len(rooms[rooms["status"] == "Đang ở"])
    cleaning = len(rooms[rooms["status"] == "Đang dọn"])
    maintenance = len(rooms[rooms["status"] == "Bảo trì"])

    occupancy = 0

    if total > 0:
        occupancy = round((occupied / total) * 100, 1)

    cols = st.columns(6)

    with cols[0]:
        metric_card("Tổng phòng", total, "Phòng trong hệ thống")

    with cols[1]:
        metric_card("Phòng trống", empty, "Có thể bán")

    with cols[2]:
        metric_card("Đã đặt", booked, "Khách đã đặt")

    with cols[3]:
        metric_card("Đang ở", occupied, "Khách đang lưu trú")

    with cols[4]:
        metric_card("Đang dọn", cleaning, "Housekeeping")

    with cols[5]:
        metric_card("Bảo trì", maintenance, "Không bán")

    st.markdown(
        '<div class="section-title">📊 Tình hình phòng</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Tỷ lệ sử dụng phòng")
        st.progress(min(occupancy / 100, 1.0))
        st.write(f"**{occupancy}%** phòng đang có khách")

    with col2:
        status_data = pd.DataFrame({
            "Trạng thái": [
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Đang dọn",
                "Bảo trì"
            ],
            "Số phòng": [
                empty,
                booked,
                occupied,
                cleaning,
                maintenance
            ]
        })

        st.bar_chart(
            status_data.set_index("Trạng thái")
        )

    st.markdown(
        '<div class="section-title">🚪 Phòng đang có khách</div>',
        unsafe_allow_html=True
    )

    occupied_rooms = rooms[
        rooms["status"] == "Đang ở"
    ]

    if occupied_rooms.empty:
        st.info("Hiện chưa có phòng nào đang có khách.")

    else:
        for _, room in occupied_rooms.iterrows():

            col1, col2, col3, col4 = st.columns(
                [1, 2, 1, 1]
            )

            with col1:
                st.markdown(
                    f"### 🚪 {room['room_number']}"
                )

            with col2:
                st.write(
                    f"**{room['guest_name']}**"
                )

            with col3:
                st.write(
                    f"Check-in: {room['check_in']}"
                )

            with col4:
                st.write(
                    f"Check-out: {room['check_out']}"
                )


# ============================================================
# ROOM MANAGEMENT
# ============================================================

def room_management():
    st.title("🚪 Quản lý phòng")

    rooms = get_rooms()

    col1, col2, col3 = st.columns(3)

    with col1:
        search = st.text_input(
            "🔎 Tìm phòng",
            placeholder="Nhập số phòng..."
        )

    with col2:
        status_filter = st.selectbox(
            "Trạng thái",
            ["Tất cả"] + ROOM_STATUSES
        )

    with col3:
        floor_options = ["Tất cả"] + sorted(
            rooms["floor"].unique().tolist()
        )

        floor_filter = st.selectbox(
            "Tầng",
            floor_options
        )

    filtered = rooms.copy()

    if search:
        filtered = filtered[
            filtered["room_number"]
            .astype(str)
            .str.contains(search, case=False)
        ]

    if status_filter != "Tất cả":
        filtered = filtered[
            filtered["status"] == status_filter
        ]

    if floor_filter != "Tất cả":
        filtered = filtered[
            filtered["floor"] == floor_filter
        ]

    st.write(
        f"Hiển thị **{len(filtered)}** phòng."
    )

    # Hiển thị dạng card
    for _, room in filtered.iterrows():

        with st.container(border=True):

            col1, col2, col3, col4, col5 = st.columns(
                [1, 2, 2, 2, 1]
            )

            with col1:
                st.markdown(
                    f"### {room['room_number']}"
                )
                st.caption(
                    f"Tầng {room['floor']}"
                )

            with col2:
                st.write(
                    f"**{room['room_type']}**"
                )
                st.caption(
                    format_money(room["price"]) + "/đêm"
                )

            with col3:
                st.markdown(
                    status_badge(room["status"]),
                    unsafe_allow_html=True
                )

                if room["guest_name"]:
                    st.caption(
                        f"👤 {room['guest_name']}"
                    )

            with col4:
                if room["note"]:
                    st.caption(
                        f"📝 {room['note']}"
                    )
                else:
                    st.caption("Không có ghi chú")

            with col5:
                if st.button(
                    "Chi tiết",
                    key=f"detail_{room['id']}"
                ):
                    st.session_state[
                        "selected_room"
                    ] = room["room_number"]

                    st.rerun()

    # Chi tiết phòng
    if "selected_room" in st.session_state:

        room_number = st.session_state["selected_room"]
        room = get_room(room_number)

        if room:

            st.divider()

            st.subheader(
                f"🏨 Chi tiết phòng {room_number}"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    f"**Loại phòng:** {room['room_type']}"
                )

                st.write(
                    f"**Giá:** {format_money(room['price'])}/đêm"
                )

                st.write(
                    f"**Trạng thái:** {room['status']}"
                )

                st.write(
                    f"**Khách:** "
                    f"{room['guest_name'] or 'Chưa có'}"
                )

            with col2:

                if room["guest_phone"]:
                    st.write(
                        f"**Số điện thoại:** "
                        f"{room['guest_phone']}"
                    )

                if room["check_in"]:
                    st.write(
                        f"**Check-in:** "
                        f"{room['check_in']}"
                    )

                if room["check_out"]:
                    st.write(
                        f"**Check-out:** "
                        f"{room['check_out']}"
                    )

                st.write(
                    f"**Ghi chú:** "
                    f"{room['note'] or 'Không có'}"
                )

            st.markdown("### Cập nhật trạng thái")

            new_status = st.selectbox(
                "Chọn trạng thái mới",
                ROOM_STATUSES,
                index=ROOM_STATUSES.index(room["status"]),
                key=f"status_{room_number}"
            )

            if st.button(
                "💾 Lưu trạng thái",
                key=f"save_status_{room_number}"
            ):
                update_room_status(
                    room_number,
                    new_status
                )

                st.success(
                    "Đã cập nhật trạng thái phòng."
                )

                st.rerun()


# ============================================================
# CHECK-IN / CHECK-OUT
# ============================================================

def checkin_checkout():
    st.title("🛎️ Check-in / Check-out")

    tab1, tab2 = st.tabs([
        "🟢 Check-in",
        "🔴 Check-out"
    ])

    rooms = get_rooms()

    # --------------------------------------------------------
    # CHECK-IN
    # --------------------------------------------------------

    with tab1:

        available_rooms = rooms[
            rooms["status"] == "Trống"
        ]

        if available_rooms.empty:
            st.warning(
                "Hiện không có phòng trống để check-in."
            )

        else:

            st.subheader("Thông tin khách nhận phòng")

            with st.form("checkin_form"):

                col1, col2 = st.columns(2)

                with col1:

                    room_number = st.selectbox(
                        "Phòng",
                        available_rooms[
                            "room_number"
                        ].tolist()
                    )

                    guest_name = st.text_input(
                        "Họ và tên khách *"
                    )

                    phone = st.text_input(
                        "Số điện thoại"
                    )

                with col2:

                    check_in = st.date_input(
                        "Ngày check-in",
                        value=date.today()
                    )

                    check_out = st.date_input(
                        "Ngày check-out",
                        value=date.today()
                    )

                    note = st.text_area(
                        "Ghi chú"
                    )

                submitted = st.form_submit_button(
                    "🟢 Xác nhận Check-in",
                    use_container_width=True
                )

                if submitted:

                    if not guest_name.strip():
                        st.error(
                            "Vui lòng nhập tên khách."
                        )

                    elif check_out < check_in:
                        st.error(
                            "Ngày check-out không hợp lệ."
                        )

                    else:

                        check_in_guest(
                            room_number,
                            guest_name.strip(),
                            phone.strip(),
                            check_in.isoformat(),
                            check_out.isoformat(),
                            note.strip()
                        )

                        st.success(
                            f"Đã check-in khách "
                            f"{guest_name} vào phòng "
                            f"{room_number}."
                        )

                        st.rerun()

    # --------------------------------------------------------
    # CHECK-OUT
    # --------------------------------------------------------

    with tab2:

        occupied_rooms = rooms[
            rooms["status"] == "Đang ở"
        ]

        if occupied_rooms.empty:

            st.info(
                "Hiện không có phòng đang có khách."
            )

        else:

            for _, room in occupied_rooms.iterrows():

                with st.container(border=True):

                    col1, col2, col3, col4 = st.columns(
                        [1, 2, 2, 1]
                    )

                    with col1:
                        st.markdown(
                            f"### {room['room_number']}"
                        )

                    with col2:
                        st.write(
                            f"👤 **{room['guest_name']}**"
                        )

                    with col3:
                        st.caption(
                            f"Check-out dự kiến: "
                            f"{room['check_out']}"
                        )

                    with col4:

                        if st.button(
                            "Check-out",
                            key=f"checkout_{room['id']}"
                        ):

                            check_out_guest(
                                room["room_number"]
                            )

                            st.success(
                                "Đã check-out thành công."
                            )

                            st.rerun()


# ============================================================
# BOOKING
# ============================================================

def booking_management():
    st.title("📅 Quản lý đặt phòng")

    tab1, tab2 = st.tabs([
        "➕ Tạo đặt phòng",
        "📋 Danh sách đặt phòng"
    ])

    rooms = get_rooms()

    with tab1:

        available = rooms[
            rooms["status"] == "Trống"
        ]

        if available.empty:

            st.warning(
                "Không có phòng trống."
            )

        else:

            with st.form("booking_form"):

                col1, col2 = st.columns(2)

                with col1:

                    room_number = st.selectbox(
                        "Phòng",
                        available["room_number"].tolist()
                    )

                    guest_name = st.text_input(
                        "Tên khách *"
                    )

                    phone = st.text_input(
                        "Số điện thoại"
                    )

                    adults = st.number_input(
                        "Số người lớn",
                        min_value=1,
                        max_value=20,
                        value=1
                    )

                with col2:

                    check_in = st.date_input(
                        "Ngày nhận phòng",
                        value=date.today()
                    )

                    check_out = st.date_input(
                        "Ngày trả phòng",
                        value=date.today()
                    )

                    children = st.number_input(
                        "Số trẻ em",
                        min_value=0,
                        max_value=20,
                        value=0
                    )

                    note = st.text_area(
                        "Ghi chú"
                    )

                submitted = st.form_submit_button(
                    "📅 Tạo đặt phòng",
                    use_container_width=True
                )

                if submitted:

                    if not guest_name.strip():
                        st.error(
                            "Vui lòng nhập tên khách."
                        )

                    elif check_out <= check_in:
                        st.error(
                            "Ngày trả phòng phải sau "
                            "ngày nhận phòng."
                        )

                    else:

                        add_booking(
                            room_number,
                            guest_name.strip(),
                            phone.strip(),
                            check_in.isoformat(),
                            check_out.isoformat(),
                            adults,
                            children,
                            note.strip()
                        )

                        st.success(
                            "Tạo đặt phòng thành công."
                        )

                        st.rerun()

    with tab2:

        bookings = get_bookings()

        if bookings.empty:

            st.info(
                "Chưa có dữ liệu đặt phòng."
            )

        else:

            display = bookings[
                [
                    "id",
                    "room_number",
                    "guest_name",
                    "phone",
                    "check_in",
                    "check_out",
                    "adults",
                    "children",
                    "status",
                    "note",
                ]
            ].copy()

            display.columns = [
                "ID",
                "Phòng",
                "Khách",
                "SĐT",
                "Check-in",
                "Check-out",
                "Người lớn",
                "Trẻ em",
                "Trạng thái",
                "Ghi chú",
            ]

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# THÊM / SỬA PHÒNG
# ============================================================

def room_settings():
    st.title("⚙️ Cài đặt phòng")

    tab1, tab2, tab3 = st.tabs([
        "➕ Thêm phòng",
        "✏️ Sửa phòng",
        "🗑️ Xóa phòng"
    ])

    rooms = get_rooms()

    # --------------------------------------------------------
    # ADD
    # --------------------------------------------------------

    with tab1:

        with st.form("add_room_form"):

            col1, col2 = st.columns(2)

            with col1:

                room_number = st.text_input(
                    "Số phòng *",
                    placeholder="Ví dụ: 401"
                )

                floor = st.number_input(
                    "Tầng",
                    min_value=1,
                    max_value=100,
                    value=4
                )

                room_type = st.selectbox(
                    "Loại phòng",
                    ROOM_TYPES
                )

            with col2:

                price = st.number_input(
                    "Giá phòng / đêm (VNĐ)",
                    min_value=0,
                    value=1000000,
                    step=100000
                )

                status = st.selectbox(
                    "Trạng thái",
                    ROOM_STATUSES
                )

                note = st.text_area(
                    "Ghi chú"
                )

            submitted = st.form_submit_button(
                "➕ Thêm phòng",
                use_container_width=True
            )

            if submitted:

                if not room_number.strip():
                    st.error(
                        "Vui lòng nhập số phòng."
                    )

                else:

                    success = add_room(
                        room_number.strip(),
                        floor,
                        room_type,
                        price,
                        status,
                        note.strip()
                    )

                    if success:
                        st.success(
                            f"Đã thêm phòng "
                            f"{room_number}."
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Số phòng đã tồn tại."
                        )

    # --------------------------------------------------------
    # EDIT
    # --------------------------------------------------------

    with tab2:

        if rooms.empty:

            st.info("Chưa có phòng.")

        else:

            room_numbers = rooms[
                "room_number"
            ].tolist()

            selected = st.selectbox(
                "Chọn phòng",
                room_numbers,
                key="edit_room"
            )

            room = get_room(selected)

            if room:

                with st.form("edit_room_form"):

                    col1, col2 = st.columns(2)

                    with col1:

                        new_number = st.text_input(
                            "Số phòng",
                            value=room["room_number"]
                        )

                        new_floor = st.number_input(
                            "Tầng",
                            min_value=1,
                            max_value=100,
                            value=int(room["floor"])
                        )

                        new_type = st.selectbox(
                            "Loại phòng",
                            ROOM_TYPES,
                            index=ROOM_TYPES.index(
                                room["room_type"]
                            )
                        )

                    with col2:

                        new_price = st.number_input(
                            "Giá phòng / đêm",
                            min_value=0,
                            value=float(room["price"]),
                            step=100000.0
                        )

                        new_status = st.selectbox(
                            "Trạng thái",
                            ROOM_STATUSES,
                            index=ROOM_STATUSES.index(
                                room["status"]
                            )
                        )

                        new_note = st.text_area(
                            "Ghi chú",
                            value=room["note"] or ""
                        )

                    submitted = st.form_submit_button(
                        "💾 Lưu thay đổi",
                        use_container_width=True
                    )

                    if submitted:

                        success = update_room(
                            room["id"],
                            new_number.strip(),
                            new_floor,
                            new_type,
                            new_price,
                            new_status,
                            new_note.strip()
                        )

                        if success:
                            st.success(
                                "Đã cập nhật phòng."
                            )
                            st.rerun()

                        else:
                            st.error(
                                "Số phòng đã tồn tại."
                            )

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    with tab3:

        if rooms.empty:

            st.info("Chưa có phòng.")

        else:

            selected = st.selectbox(
                "Chọn phòng muốn xóa",
                rooms["room_number"].tolist(),
                key="delete_room"
            )

            room = get_room(selected)

            st.warning(
                f"Bạn đang chuẩn bị xóa phòng **{selected}**."
            )

            confirm = st.checkbox(
                "Tôi xác nhận muốn xóa phòng này."
            )

            if st.button(
                "🗑️ Xóa phòng",
                disabled=not confirm
            ):

                delete_room(
                    room["id"],
                    room["room_number"]
                )

                st.success(
                    "Đã xóa phòng."
                )

                st.rerun()


# ============================================================
# HOUSEKEEPING
# ============================================================

def housekeeping():
    st.title("🧹 Housekeeping")

    rooms = get_rooms()

    cleaning_rooms = rooms[
        rooms["status"] == "Đang dọn"
    ]

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card(
            "Cần dọn",
            len(cleaning_rooms),
            "Phòng chờ Housekeeping"
        )

    with col2:
        ready_rooms = rooms[
            rooms["status"] == "Trống"
        ]

        metric_card(
            "Đã sẵn sàng",
            len(ready_rooms),
            "Có thể bán"
        )

    with col3:
        maintenance = rooms[
            rooms["status"] == "Bảo trì"
        ]

        metric_card(
            "Bảo trì",
            len(maintenance),
            "Phòng không sử dụng"
        )

    st.divider()

    st.subheader("Danh sách phòng cần dọn")

    if cleaning_rooms.empty:

        st.success(
            "🎉 Hiện không có phòng cần dọn."
        )

    else:

        for _, room in cleaning_rooms.iterrows():

            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [1, 3, 1]
                )

                with col1:

                    st.markdown(
                        f"### 🚪 {room['room_number']}"
                    )

                with col2:

                    st.write(
                        f"Loại phòng: "
                        f"**{room['room_type']}**"
                    )

                    if room["note"]:
                        st.caption(
                            f"Ghi chú: {room['note']}"
                        )

                with col3:

                    if st.button(
                        "✅ Đã dọn",
                        key=f"clean_{room['id']}"
                    ):

                        update_room_status(
                            room["room_number"],
                            "Trống"
                        )

                        st.success(
                            "Phòng đã sẵn sàng."
                        )

                        st.rerun()


# ============================================================
# ACTIVITY LOG
# ============================================================

def activity_log():
    st.title("📜 Nhật ký hoạt động")

    logs = get_logs()

    if logs.empty:

        st.info(
            "Chưa có hoạt động nào."
        )

        return

    display = logs.copy()

    display.columns = [
        "ID",
        "Thao tác",
        "Phòng",
        "Mô tả",
        "Thời gian"
    ]

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# REPORT
# ============================================================

def reports():
    st.title("📊 Báo cáo")

    rooms = get_rooms()

    total = len(rooms)

    if total == 0:
        st.info("Chưa có dữ liệu phòng.")
        return

    # -------------------------
    # ROOM STATUS
    # -------------------------

    status_count = (
        rooms["status"]
        .value_counts()
        .reindex(ROOM_STATUSES, fill_value=0)
    )

    st.subheader("Tổng quan trạng thái phòng")

    report_df = pd.DataFrame({
        "Trạng thái": status_count.index,
        "Số phòng": status_count.values
    })

    col1, col2 = st.columns(2)

    with col1:

        st.dataframe(
            report_df,
            use_container_width=True,
            hide_index=True
        )

    with col2:

        st.bar_chart(
            report_df.set_index("Trạng thái")
        )

    # -------------------------
    # REVENUE POTENTIAL
    # -------------------------

    st.subheader("💰 Doanh thu phòng dự kiến")

    occupied = rooms[
        rooms["status"] == "Đang ở"
    ]

    potential = occupied["price"].sum()

    st.metric(
        "Giá trị phòng đang sử dụng / đêm",
        format_money(potential)
    )

    st.caption(
        "Đây là tổng giá niêm yết của các phòng "
        "đang ở, chưa bao gồm giảm giá, thuế, phí "
        "hoặc các dịch vụ khác."
    )

    # -------------------------
    # ROOM TYPE
    # -------------------------

    st.subheader("Phân bố loại phòng")

    type_count = (
        rooms["room_type"]
        .value_counts()
        .reset_index()
    )

    type_count.columns = [
        "Loại phòng",
        "Số phòng"
    ]

    st.dataframe(
        type_count,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    st.sidebar.markdown(
        """
        <div style="
            text-align:center;
            font-size:26px;
            font-weight:800;
            margin-bottom:25px;
        ">
        🏨 HOTEL
        </div>
        """,
        unsafe_allow_html=True
    )

    menu = st.sidebar.radio(
        "MENU",
        [
            "📊 Dashboard",
            "🚪 Quản lý phòng",
            "🛎️ Check-in / Check-out",
            "📅 Đặt phòng",
            "🧹 Housekeeping",
            "📈 Báo cáo",
            "📜 Nhật ký",
            "⚙️ Cài đặt phòng",
        ]
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "Hotel Manager v1.0"
    )

    st.sidebar.caption(
        "Quản lý phòng khách sạn"
    )

    return menu


# ============================================================
# MAIN
# ============================================================

def main():

    init_database()
    load_css()

    menu = sidebar()

    if menu == "📊 Dashboard":
        dashboard()

    elif menu == "🚪 Quản lý phòng":
        room_management()

    elif menu == "🛎️ Check-in / Check-out":
        checkin_checkout()

    elif menu == "📅 Đặt phòng":
        booking_management()

    elif menu == "🧹 Housekeeping":
        housekeeping()

    elif menu == "📈 Báo cáo":
        reports()

    elif menu == "📜 Nhật ký":
        activity_log()

    elif menu == "⚙️ Cài đặt phòng":
        room_settings()


if __name__ == "__main__":
    main()

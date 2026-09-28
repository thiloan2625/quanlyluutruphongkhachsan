import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import date, timedelta

# ============================================================
# 1. CẤU HÌNH ỨNG DỤNG
# ============================================================

st.set_page_config(
    page_title="5★ Hotel Management",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. THÔNG TIN KẾT NỐI MYSQL AIVEN
# ============================================================

DB_CONFIG = {
    "host": "mysql-16835565-phamloan20052021-5585.a.aivencloud.com",
    "port": 20173,
    "user": "avnadmin",
    "password": "AVNS_4Y53MuDonSf1vyjhBby",
    "database": "defaultdb",
    "ssl_disabled": False,
    "connection_timeout": 15
}

# ============================================================
# 3. CẤU HÌNH PHÒNG KHÁCH SẠN
# ============================================================

ROOM_STATUSES = [
    "Trống",
    "Đã đặt",
    "Đang ở",
    "Đang dọn",
    "Bảo trì"
]

ROOM_TYPES = [
    "Deluxe",
    "Premier",
    "Executive",
    "Family",
    "Junior Suite",
    "Suite",
    "Presidential Suite"
]

ROOM_PRICES = {
    "Deluxe": 2500000,
    "Premier": 3200000,
    "Executive": 4200000,
    "Family": 4800000,
    "Junior Suite": 6000000,
    "Suite": 8500000,
    "Presidential Suite": 12000000
}

STATUS_COLORS = {
    "Trống": "#16a34a",
    "Đã đặt": "#2563eb",
    "Đang ở": "#f59e0b",
    "Đang dọn": "#7c3aed",
    "Bảo trì": "#dc2626"
}


# ============================================================
# 4. KẾT NỐI DATABASE
# ============================================================

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def execute_query(query, params=None, fetch=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(query, params or ())

        if fetch:
            result = cursor.fetchall()
            return result

        conn.commit()
        return True

    finally:
        cursor.close()
        conn.close()


def get_dataframe(query, params=None):
    conn = get_connection()

    try:
        return pd.read_sql(
            query,
            conn,
            params=params
        )
    finally:
        conn.close()


# ============================================================
# 5. KHỞI TẠO DATABASE
# ============================================================

def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_number VARCHAR(20) UNIQUE NOT NULL,
                floor INT NOT NULL,
                room_type VARCHAR(100) NOT NULL,
                price DECIMAL(15,2) NOT NULL,
                status VARCHAR(30) DEFAULT 'Trống',
                guest_name VARCHAR(255) DEFAULT '',
                guest_phone VARCHAR(30) DEFAULT '',
                guest_email VARCHAR(255) DEFAULT '',
                check_in DATE NULL,
                check_out DATE NULL,
                adults INT DEFAULT 0,
                children INT DEFAULT 0,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_number VARCHAR(20) NOT NULL,
                guest_name VARCHAR(255) NOT NULL,
                phone VARCHAR(30),
                email VARCHAR(255),
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                adults INT DEFAULT 1,
                children INT DEFAULT 0,
                room_price DECIMAL(15,2) DEFAULT 0,
                status VARCHAR(30) DEFAULT 'Đã đặt',
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                action VARCHAR(100) NOT NULL,
                room_number VARCHAR(20),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

        # Kiểm tra số lượng phòng
        cursor.execute(
            "SELECT COUNT(*) AS total FROM rooms"
        )

        count = cursor.fetchone()[0]

        # ====================================================
        # TẠO 200 PHÒNG MẪU NẾU DATABASE CHƯA CÓ PHÒNG
        # ====================================================

        if count == 0:

            sample_rooms = []

            for floor in range(1, 11):

                for room_index in range(1, 21):

                    room_number = f"{floor}{room_index:02d}"

                    if room_index <= 8:
                        room_type = "Deluxe"

                    elif room_index <= 12:
                        room_type = "Premier"

                    elif room_index <= 15:
                        room_type = "Executive"

                    elif room_index <= 17:
                        room_type = "Family"

                    elif room_index == 18:
                        room_type = "Junior Suite"

                    elif room_index == 19:
                        room_type = "Suite"

                    else:
                        room_type = "Presidential Suite"

                    price = ROOM_PRICES[room_type]

                    position = (
                        (floor - 1) * 20 + room_index
                    )

                    remainder = position % 20

                    if remainder in [1, 2, 3, 4, 5]:
                        status = "Đang ở"

                    elif remainder in [6, 7, 8, 9]:
                        status = "Đã đặt"

                    elif remainder in [10, 11]:
                        status = "Đang dọn"

                    elif remainder == 12:
                        status = "Bảo trì"

                    else:
                        status = "Trống"

                    if status in ["Đang ở", "Đã đặt"]:

                        guest_name = f"Khách {room_number}"
                        guest_phone = f"090{floor:02d}{room_index:04d}"
                        guest_email = f"guest{room_number}@example.com"

                        check_in = date.today()

                        check_out = (
                            date.today()
                            + timedelta(days=2)
                        )

                        adults = 2
                        children = 0

                    else:

                        guest_name = ""
                        guest_phone = ""
                        guest_email = ""
                        check_in = None
                        check_out = None
                        adults = 0
                        children = 0

                    if status == "Đang dọn":
                        note = "Housekeeping đang vệ sinh"

                    elif status == "Bảo trì":
                        note = "Đang kiểm tra kỹ thuật"

                    else:
                        note = ""

                    sample_rooms.append((
                        room_number,
                        floor,
                        room_type,
                        price,
                        status,
                        guest_name,
                        guest_phone,
                        guest_email,
                        check_in,
                        check_out,
                        adults,
                        children,
                        note
                    ))

            cursor.executemany("""
                INSERT INTO rooms (
                    room_number,
                    floor,
                    room_type,
                    price,
                    status,
                    guest_name,
                    guest_phone,
                    guest_email,
                    check_in,
                    check_out,
                    adults,
                    children,
                    note
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
            """, sample_rooms)

            conn.commit()

    finally:
        cursor.close()
        conn.close()


# ============================================================
# 6. LẤY DỮ LIỆU
# ============================================================

def get_rooms():
    return get_dataframe("""
        SELECT *
        FROM rooms
        ORDER BY floor, room_number
    """)


def get_room(room_number):

    result = execute_query(
        """
        SELECT *
        FROM rooms
        WHERE room_number = %s
        """,
        (room_number,),
        fetch=True
    )

    return result[0] if result else None


def get_bookings():
    return get_dataframe("""
        SELECT *
        FROM bookings
        ORDER BY check_in ASC, id DESC
    """)


def get_logs():
    return get_dataframe("""
        SELECT *
        FROM activity_logs
        ORDER BY id DESC
        LIMIT 200
    """)


# ============================================================
# 7. NHẬT KÝ HOẠT ĐỘNG
# ============================================================

def log_activity(action, room_number="", description=""):

    execute_query(
        """
        INSERT INTO activity_logs (
            action,
            room_number,
            description
        )
        VALUES (%s, %s, %s)
        """,
        (
            action,
            room_number,
            description
        )
    )


# ============================================================
# 8. QUẢN LÝ TRẠNG THÁI PHÒNG
# ============================================================

def update_room_status(room_number, new_status):

    execute_query(
        """
        UPDATE rooms
        SET status = %s
        WHERE room_number = %s
        """,
        (
            new_status,
            room_number
        )
    )

    log_activity(
        "Cập nhật trạng thái",
        room_number,
        f"Trạng thái mới: {new_status}"
    )


# ============================================================
# 9. CHECK-IN
# ============================================================

def check_in_guest(
    room_number,
    guest_name,
    phone,
    email,
    check_in,
    check_out,
    adults,
    children,
    note
):

    execute_query(
        """
        UPDATE rooms
        SET
            status = 'Đang ở',
            guest_name = %s,
            guest_phone = %s,
            guest_email = %s,
            check_in = %s,
            check_out = %s,
            adults = %s,
            children = %s,
            note = %s
        WHERE room_number = %s
        """,
        (
            guest_name,
            phone,
            email,
            check_in,
            check_out,
            adults,
            children,
            note,
            room_number
        )
    )

    log_activity(
        "Check-in",
        room_number,
        f"Khách nhận phòng: {guest_name}"
    )


# ============================================================
# 10. CHECK-OUT
# ============================================================

def check_out_guest(room_number):

    room = get_room(room_number)

    if room is None:
        return

    guest_name = room["guest_name"]

    execute_query(
        """
        UPDATE rooms
        SET
            status = 'Đang dọn',
            guest_name = '',
            guest_phone = '',
            guest_email = '',
            check_in = NULL,
            check_out = NULL,
            adults = 0,
            children = 0
        WHERE room_number = %s
        """,
        (room_number,)
    )

    log_activity(
        "Check-out",
        room_number,
        f"Khách trả phòng: {guest_name}"
    )


# ============================================================
# 11. ĐẶT PHÒNG
# ============================================================

def create_booking(
    room_number,
    guest_name,
    phone,
    email,
    check_in,
    check_out,
    adults,
    children,
    room_price,
    note
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO bookings (
                room_number,
                guest_name,
                phone,
                email,
                check_in,
                check_out,
                adults,
                children,
                room_price,
                status,
                note
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, 'Đã đặt', %s
            )
        """, (
            room_number,
            guest_name,
            phone,
            email,
            check_in,
            check_out,
            adults,
            children,
            room_price,
            note
        ))

        cursor.execute("""
            UPDATE rooms
            SET
                status = 'Đã đặt',
                guest_name = %s,
                guest_phone = %s,
                guest_email = %s,
                check_in = %s,
                check_out = %s,
                adults = %s,
                children = %s
            WHERE room_number = %s
        """, (
            guest_name,
            phone,
            email,
            check_in,
            check_out,
            adults,
            children,
            room_number
        ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

    log_activity(
        "Tạo đặt phòng",
        room_number,
        f"Khách: {guest_name}"
    )


# ============================================================
# 12. THÊM PHÒNG
# ============================================================

def add_room(
    room_number,
    floor,
    room_type,
    price,
    status,
    note
):

    try:

        execute_query(
            """
            INSERT INTO rooms (
                room_number,
                floor,
                room_type,
                price,
                status,
                note
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                room_number,
                floor,
                room_type,
                price,
                status,
                note
            )
        )

        log_activity(
            "Thêm phòng",
            room_number,
            f"Loại phòng: {room_type}"
        )

        return True

    except Error:
        return False


# ============================================================
# 13. SỬA PHÒNG
# ============================================================

def update_room(
    room_id,
    room_number,
    floor,
    room_type,
    price,
    status,
    note
):

    try:

        execute_query(
            """
            UPDATE rooms
            SET
                room_number = %s,
                floor = %s,
                room_type = %s,
                price = %s,
                status = %s,
                note = %s
            WHERE id = %s
            """,
            (
                room_number,
                floor,
                room_type,
                price,
                status,
                note,
                room_id
            )
        )

        log_activity(
            "Sửa phòng",
            room_number,
            "Thông tin phòng được cập nhật"
        )

        return True

    except Error:
        return False


# ============================================================
# 14. XÓA PHÒNG
# ============================================================

def delete_room(room_id, room_number):

    execute_query(
        """
        DELETE FROM rooms
        WHERE id = %s
        """,
        (room_id,)
    )

    log_activity(
        "Xóa phòng",
        room_number,
        "Đã xóa phòng"
    )


# ============================================================
# 15. ĐỊNH DẠNG
# ============================================================

def money(value):

    return (
        f"{float(value):,.0f}"
        .replace(",", ".")
        + " VNĐ"
    )


def status_badge(status):

    color = STATUS_COLORS.get(
        status,
        "#6b7280"
    )

    return f"""
    <span style="
        background:{color};
        color:white;
        padding:5px 12px;
        border-radius:20px;
        font-size:12px;
        font-weight:700;
    ">
        {status}
    </span>
    """


# ============================================================
# 16. GIAO DIỆN CSS
# ============================================================

def load_css():

    st.markdown("""
        <style>

        .main {
            background-color: #f6f7fb;
        }

        [data-testid="stSidebar"] {
            background: #111827;
        }

        [data-testid="stSidebar"] * {
            color: white;
        }

        .hotel-title {
            font-size: 34px;
            font-weight: 800;
            color: #111827;
        }

        .hotel-subtitle {
            color: #6b7280;
            margin-bottom: 25px;
        }

        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #e5e7eb;
            min-height: 125px;
        }

        .metric-title {
            color: #6b7280;
            font-size: 14px;
        }

        .metric-number {
            font-size: 30px;
            font-weight: 800;
            margin-top: 7px;
        }

        </style>
    """, unsafe_allow_html=True)


def metric_card(title, number, description=""):

    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-number">{number}</div>
            <div style="color:#9ca3af;font-size:12px;">
                {description}
            </div>
        </div>
    """, unsafe_allow_html=True)


# ============================================================
# 17. DASHBOARD
# ============================================================

def dashboard():

    st.markdown(
        '<div class="hotel-title">🏨 5★ HOTEL MANAGEMENT</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="hotel-subtitle">'
        'Hệ thống quản lý vận hành khách sạn'
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

    occupancy = (
        round(occupied / total * 100, 1)
        if total else 0
    )

    cols = st.columns(6)

    metrics = [
        ("Tổng phòng", total, "Phòng"),
        ("Phòng trống", empty, "Có thể bán"),
        ("Đã đặt", booked, "Reservation"),
        ("Đang ở", occupied, "Occupied"),
        ("Đang dọn", cleaning, "Housekeeping"),
        ("Bảo trì", maintenance, "Out of order")
    ]

    for col, metric in zip(cols, metrics):
        with col:
            metric_card(*metric)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📈 Công suất phòng")

        st.progress(
            min(occupancy / 100, 1)
        )

        st.write(
            f"**{occupancy}%** phòng đang có khách"
        )

    with col2:

        status_data = pd.DataFrame({
            "Trạng thái": ROOM_STATUSES,
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

    occupied_rooms = rooms[
        rooms["status"] == "Đang ở"
    ]

    room_revenue = occupied_rooms["price"].sum()

    st.subheader("💰 Doanh thu phòng đang sử dụng")

    st.metric(
        "Giá phòng dự kiến / đêm",
        money(room_revenue)
    )

    st.caption(
        "Giá trị tham khảo theo giá niêm yết, "
        "chưa bao gồm thuế, phí và dịch vụ bổ sung."
    )

    st.subheader("👤 Khách đang lưu trú")

    if occupied_rooms.empty:
        st.info("Hiện chưa có khách lưu trú.")
    else:

        display = occupied_rooms[
            [
                "room_number",
                "room_type",
                "guest_name",
                "guest_phone",
                "check_in",
                "check_out"
            ]
        ].copy()

        display.columns = [
            "Phòng",
            "Loại phòng",
            "Khách",
            "Điện thoại",
            "Check-in",
            "Check-out"
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 18. QUẢN LÝ PHÒNG
# ============================================================

def room_management():

    st.title("🚪 Quản lý phòng")

    rooms = get_rooms()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        search = st.text_input(
            "🔎 Tìm phòng",
            placeholder="101, 205..."
        )

    with col2:
        status_filter = st.selectbox(
            "Trạng thái",
            ["Tất cả"] + ROOM_STATUSES
        )

    with col3:
        type_filter = st.selectbox(
            "Loại phòng",
            ["Tất cả"] + ROOM_TYPES
        )

    with col4:
        floor_filter = st.selectbox(
            "Tầng",
            ["Tất cả"] + sorted(
                rooms["floor"].unique().tolist()
            )
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

    if type_filter != "Tất cả":
        filtered = filtered[
            filtered["room_type"] == type_filter
        ]

    if floor_filter != "Tất cả":
        filtered = filtered[
            filtered["floor"] == floor_filter
        ]

    st.write(
        f"Hiển thị **{len(filtered)}** phòng"
    )

    display = filtered[
        [
            "room_number",
            "floor",
            "room_type",
            "price",
            "status",
            "guest_name",
            "check_in",
            "check_out",
            "note"
        ]
    ].copy()

    display["price"] = display["price"].apply(money)

    display.columns = [
        "Phòng",
        "Tầng",
        "Loại phòng",
        "Giá/đêm",
        "Trạng thái",
        "Khách",
        "Check-in",
        "Check-out",
        "Ghi chú"
    ]

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    if not filtered.empty:

        selected_room = st.selectbox(
            "Chọn phòng xem chi tiết",
            filtered["room_number"].tolist()
        )

        room = get_room(selected_room)

        if room:

            col1, col2 = st.columns(2)

            with col1:

                st.subheader(
                    f"🚪 Phòng {room['room_number']}"
                )

                st.write(
                    f"**Tầng:** {room['floor']}"
                )

                st.write(
                    f"**Loại:** {room['room_type']}"
                )

                st.write(
                    f"**Giá:** {money(room['price'])}/đêm"
                )

                st.markdown(
                    status_badge(room["status"]),
                    unsafe_allow_html=True
                )

            with col2:

                st.write(
                    f"**Khách:** {room['guest_name'] or '—'}"
                )

                st.write(
                    f"**Điện thoại:** {room['guest_phone'] or '—'}"
                )

                st.write(
                    f"**Email:** {room['guest_email'] or '—'}"
                )

                st.write(
                    f"**Ghi chú:** {room['note'] or '—'}"
                )

            new_status = st.selectbox(
                "Cập nhật trạng thái",
                ROOM_STATUSES,
                index=ROOM_STATUSES.index(room["status"])
            )

            if st.button("💾 Lưu trạng thái"):

                update_room_status(
                    selected_room,
                    new_status
                )

                st.success("Đã cập nhật trạng thái.")

                st.rerun()


# ============================================================
# 19. CHECK-IN / CHECK-OUT
# ============================================================

def checkin_checkout():

    st.title("🛎️ Check-in / Check-out")

    tab1, tab2 = st.tabs([
        "🟢 Check-in",
        "🔴 Check-out"
    ])

    rooms = get_rooms()

    with tab1:

        available = rooms[
            rooms["status"] == "Trống"
        ]

        if available.empty:

            st.warning("Không có phòng trống.")

        else:

            with st.form("checkin_form"):

                st.subheader("Thông tin khách")

                col1, col2 = st.columns(2)

                with col1:

                    room_number = st.selectbox(
                        "Phòng",
                        available["room_number"].tolist()
                    )

                    guest_name = st.text_input(
                        "Họ tên khách *"
                    )

                    phone = st.text_input(
                        "Số điện thoại"
                    )

                    email = st.text_input(
                        "Email"
                    )

                with col2:

                    check_in = st.date_input(
                        "Ngày check-in",
                        date.today()
                    )

                    check_out = st.date_input(
                        "Ngày check-out",
                        date.today() + timedelta(days=1)
                    )

                    adults = st.number_input(
                        "Người lớn",
                        1, 20, 1
                    )

                    children = st.number_input(
                        "Trẻ em",
                        0, 20, 0
                    )

                note = st.text_area("Ghi chú")

                submit = st.form_submit_button(
                    "🟢 Xác nhận Check-in",
                    use_container_width=True
                )

                if submit:

                    if not guest_name.strip():

                        st.error("Vui lòng nhập tên khách.")

                    elif check_out <= check_in:

                        st.error(
                            "Ngày check-out phải sau ngày check-in."
                        )

                    else:

                        check_in_guest(
                            room_number,
                            guest_name.strip(),
                            phone.strip(),
                            email.strip(),
                            check_in,
                            check_out,
                            adults,
                            children,
                            note.strip()
                        )

                        st.success(
                            f"Check-in thành công phòng {room_number}."
                        )

                        st.rerun()

    with tab2:

        occupied = rooms[
            rooms["status"] == "Đang ở"
        ]

        if occupied.empty:

            st.info("Không có khách đang lưu trú.")

        else:

            for _, room in occupied.iterrows():

                with st.container(border=True):

                    col1, col2, col3, col4 = st.columns(
                        [1, 3, 2, 1]
                    )

                    with col1:
                        st.markdown(
                            f"### {room['room_number']}"
                        )

                    with col2:
                        st.write(
                            f"👤 **{room['guest_name']}**"
                        )

                        st.caption(room["guest_phone"])

                    with col3:
                        st.caption(
                            f"Check-in: {room['check_in']}"
                        )

                        st.caption(
                            f"Check-out: {room['check_out']}"
                        )

                    with col4:

                        if st.button(
                            "Check-out",
                            key=f"out_{room['id']}"
                        ):

                            check_out_guest(
                                room["room_number"]
                            )

                            st.success(
                                "Check-out thành công."
                            )

                            st.rerun()


# ============================================================
# 20. QUẢN LÝ ĐẶT PHÒNG
# ============================================================

def booking_management():

    st.title("📅 Quản lý đặt phòng")

    tab1, tab2 = st.tabs([
        "➕ Tạo đặt phòng",
        "📋 Danh sách"
    ])

    rooms = get_rooms()

    with tab1:

        available = rooms[
            rooms["status"] == "Trống"
        ]

        if available.empty:

            st.warning("Không còn phòng trống.")

        else:

            with st.form("booking_form"):

                col1, col2 = st.columns(2)

                with col1:

                    room_number = st.selectbox(
                        "Phòng",
                        available["room_number"].tolist()
                    )

                    room = get_room(room_number)

                    st.info(
                        f"Giá phòng: {money(room['price'])}/đêm"
                    )

                    guest_name = st.text_input(
                        "Tên khách *"
                    )

                    phone = st.text_input(
                        "Số điện thoại"
                    )

                    email = st.text_input("Email")

                with col2:

                    check_in = st.date_input(
                        "Ngày nhận phòng",
                        date.today()
                    )

                    check_out = st.date_input(
                        "Ngày trả phòng",
                        date.today() + timedelta(days=1)
                    )

                    adults = st.number_input(
                        "Người lớn",
                        1, 20, 1
                    )

                    children = st.number_input(
                        "Trẻ em",
                        0, 20, 0
                    )

                note = st.text_area("Ghi chú")

                submit = st.form_submit_button(
                    "📅 Xác nhận đặt phòng",
                    use_container_width=True
                )

                if submit:

                    if not guest_name.strip():

                        st.error("Vui lòng nhập tên khách.")

                    elif check_out <= check_in:

                        st.error(
                            "Ngày trả phòng phải sau ngày nhận phòng."
                        )

                    else:

                        create_booking(
                            room_number,
                            guest_name.strip(),
                            phone.strip(),
                            email.strip(),
                            check_in,
                            check_out,
                            adults,
                            children,
                            room["price"],
                            note.strip()
                        )

                        st.success(
                            "Đặt phòng thành công."
                        )

                        st.rerun()

    with tab2:

        bookings = get_bookings()

        if bookings.empty:

            st.info("Chưa có đặt phòng.")

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
                    "room_price",
                    "status"
                ]
            ].copy()

            display["room_price"] = display[
                "room_price"
            ].apply(money)

            display.columns = [
                "ID",
                "Phòng",
                "Khách",
                "SĐT",
                "Check-in",
                "Check-out",
                "Người lớn",
                "Trẻ em",
                "Giá/đêm",
                "Trạng thái"
            ]

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# 21. HOUSEKEEPING
# ============================================================

def housekeeping():

    st.title("🧹 Housekeeping")

    rooms = get_rooms()

    cleaning = rooms[
        rooms["status"] == "Đang dọn"
    ]

    maintenance = rooms[
        rooms["status"] == "Bảo trì"
    ]

    ready = rooms[
        rooms["status"] == "Trống"
    ]

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card(
            "Cần dọn",
            len(cleaning),
            "Phòng"
        )

    with col2:
        metric_card(
            "Sẵn sàng",
            len(ready),
            "Phòng"
        )

    with col3:
        metric_card(
            "Bảo trì",
            len(maintenance),
            "Phòng"
        )

    st.divider()

    st.subheader("🧹 Phòng đang dọn")

    if cleaning.empty:

        st.success("Không có phòng cần dọn.")

    else:

        for _, room in cleaning.iterrows():

            with st.container(border=True):

                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    st.markdown(
                        f"### {room['room_number']}"
                    )

                with col2:
                    st.write(
                        f"**{room['room_type']}**"
                    )

                    st.caption(room["note"])

                with col3:

                    if st.button(
                        "✅ Hoàn tất",
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

    st.divider()

    st.subheader("🔧 Phòng bảo trì")

    if maintenance.empty:

        st.success("Không có phòng bảo trì.")

    else:

        for _, room in maintenance.iterrows():

            with st.container(border=True):

                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    st.markdown(
                        f"### {room['room_number']}"
                    )

                with col2:
                    st.write(room["room_type"])
                    st.caption(room["note"])

                with col3:

                    if st.button(
                        "🔓 Hoàn tất",
                        key=f"repair_{room['id']}"
                    ):

                        update_room_status(
                            room["room_number"],
                            "Trống"
                        )

                        st.success(
                            "Phòng đã hoạt động lại."
                        )

                        st.rerun()


# ============================================================
# 22. BÁO CÁO
# ============================================================

def reports():

    st.title("📊 Báo cáo & doanh thu")

    rooms = get_rooms()

    total = len(rooms)

    occupied = len(
        rooms[rooms["status"] == "Đang ở"]
    )

    occupancy = (
        occupied / total * 100
        if total else 0
    )

    room_revenue = rooms[
        rooms["status"] == "Đang ở"
    ]["price"].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Tổng phòng", total)

    with col2:
        st.metric("Đang ở", occupied)

    with col3:
        st.metric("Công suất", f"{occupancy:.1f}%")

    with col4:
        st.metric(
            "Doanh thu / đêm",
            money(room_revenue)
        )

    st.divider()

    st.subheader("Trạng thái phòng")

    status_count = (
        rooms["status"]
        .value_counts()
        .reindex(ROOM_STATUSES, fill_value=0)
    )

    status_df = pd.DataFrame({
        "Trạng thái": status_count.index,
        "Số phòng": status_count.values
    })

    col1, col2 = st.columns(2)

    with col1:
        st.dataframe(
            status_df,
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.bar_chart(
            status_df.set_index("Trạng thái")
        )

    st.subheader("💰 Doanh thu theo loại phòng")

    type_report = (
        rooms[rooms["status"] == "Đang ở"]
        .groupby("room_type")
        .agg(
            Số_phòng=("room_number", "count"),
            Doanh_thu=("price", "sum")
        )
        .reset_index()
    )

    type_report["Doanh_thu"] = (
        type_report["Doanh_thu"].apply(money)
    )

    type_report.columns = [
        "Loại phòng",
        "Số phòng đang ở",
        "Doanh thu / đêm"
    ]

    st.dataframe(
        type_report,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("🏨 Giá trị toàn bộ phòng")

    inventory_value = rooms["price"].sum()

    st.metric(
        "Tổng giá niêm yết / đêm",
        money(inventory_value)
    )


# ============================================================
# 23. CÀI ĐẶT PHÒNG
# ============================================================

def room_settings():

    st.title("⚙️ Quản lý danh mục phòng")

    rooms = get_rooms()

    tab1, tab2, tab3 = st.tabs([
        "➕ Thêm phòng",
        "✏️ Sửa phòng",
        "🗑️ Xóa phòng"
    ])

    # --------------------------------------------------------
    # THÊM PHÒNG
    # --------------------------------------------------------

    with tab1:

        with st.form("add_room"):

            col1, col2 = st.columns(2)

            with col1:

                room_number = st.text_input(
                    "Số phòng *",
                    placeholder="Ví dụ: 1101"
                )

                floor = st.number_input(
                    "Tầng",
                    1, 100, 11
                )

                room_type = st.selectbox(
                    "Loại phòng",
                    ROOM_TYPES
                )

            with col2:

                price = st.number_input(
                    "Giá / đêm",
                    min_value=0,
                    value=ROOM_PRICES["Deluxe"],
                    step=100000
                )

                status = st.selectbox(
                    "Trạng thái",
                    ROOM_STATUSES
                )

                note = st.text_area("Ghi chú")

            submit = st.form_submit_button(
                "➕ Thêm phòng",
                use_container_width=True
            )

            if submit:

                if not room_number.strip():

                    st.error("Vui lòng nhập số phòng.")

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

                        st.success("Đã thêm phòng.")

                        st.rerun()

                    else:

                        st.error(
                            "Số phòng đã tồn tại hoặc dữ liệu không hợp lệ."
                        )

    # --------------------------------------------------------
    # SỬA PHÒNG
    # --------------------------------------------------------

    with tab2:

        if rooms.empty:

            st.info("Chưa có phòng.")

        else:

            selected = st.selectbox(
                "Chọn phòng",
                rooms["room_number"].tolist(),
                key="edit"
            )

            room = get_room(selected)

            with st.form("edit_form"):

                col1, col2 = st.columns(2)

                with col1:

                    new_number = st.text_input(
                        "Số phòng",
                        room["room_number"]
                    )

                    new_floor = st.number_input(
                        "Tầng",
                        1, 100,
                        int(room["floor"])
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
                        "Giá / đêm",
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
                        room["note"] or ""
                    )

                submit = st.form_submit_button(
                    "💾 Lưu thay đổi",
                    use_container_width=True
                )

                if submit:

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
                            "Không thể cập nhật. "
                            "Số phòng có thể đã tồn tại."
                        )

    # --------------------------------------------------------
    # XÓA PHÒNG
    # --------------------------------------------------------

    with tab3:

        if rooms.empty:

            st.info("Chưa có phòng.")

        else:

            selected = st.selectbox(
                "Chọn phòng",
                rooms["room_number"].tolist(),
                key="delete"
            )

            room = get_room(selected)

            st.warning(
                f"Bạn chuẩn bị xóa phòng **{selected}**."
            )

            confirm = st.checkbox(
                "Tôi xác nhận xóa phòng."
            )

            if st.button(
                "🗑️ Xóa phòng",
                disabled=not confirm
            ):

                delete_room(
                    room["id"],
                    room["room_number"]
                )

                st.success("Đã xóa phòng.")

                st.rerun()


# ============================================================
# 24. NHẬT KÝ
# ============================================================

def activity_log():

    st.title("📜 Nhật ký hoạt động")

    logs = get_logs()

    if logs.empty:

        st.info("Chưa có dữ liệu.")

        return

    logs.columns = [
        "ID",
        "Thao tác",
        "Phòng",
        "Mô tả",
        "Thời gian"
    ]

    st.dataframe(
        logs,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 25. SIDEBAR
# ============================================================

def sidebar():

    st.sidebar.markdown("""
        <div style="
            text-align:center;
            font-size:25px;
            font-weight:800;
            margin-bottom:20px;
        ">
            🏨 5★ HOTEL
        </div>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio(
        "QUẢN LÝ",
        [
            "📊 Dashboard",
            "🚪 Quản lý phòng",
            "🛎️ Check-in / Check-out",
            "📅 Đặt phòng",
            "🧹 Housekeeping",
            "📈 Báo cáo",
            "📜 Nhật ký",
            "⚙️ Cài đặt phòng"
        ]
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "Hotel Management System"
    )

    st.sidebar.caption(
        "200 rooms • 10 floors"
    )

    st.sidebar.caption(
        "MySQL Aiven Cloud"
    )

    return menu


# ============================================================
# 26. MAIN
# ============================================================

def main():

    try:

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

    except Error as e:

        st.error(
            "Không thể kết nối MySQL Aiven."
        )

        st.exception(e)

        st.info(
            "Hãy kiểm tra host, port, username, "
            "password, tên database và trạng thái "
            "dịch vụ MySQL trên Aiven."
        )


if __name__ == "__main__":
    main()

import streamlit as st
import folium
from streamlit_folium import st_folium
import networkx as nx
from geopy.distance import geodesic
import base64
from PIL import Image
import io
import matplotlib.pyplot as plt
import numpy as np
import json
import os

# Fungsi untuk encode image ke base64
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Fungsi untuk decode base64 ke image
def decode_image(encoded_str):
    return Image.open(io.BytesIO(base64.b64decode(encoded_str)))

# Fungsi untuk load profiles dari file
def load_profiles():
    if os.path.exists("profiles.json"):
        with open("profiles.json", "r") as f:
            data = json.load(f)
            for profile in data:
                if profile["photo"]:
                    profile["photo"] = decode_image(profile["photo"])
            return data
    return [
        {"name": "Pembuat 1", "student_id": "12345678", "university": "Universitas Indonesia", "major": "Informatika", "year": "2020", "contribution": "Pengembang UI dan Graph Theory", "photo": None},
        {"name": "Pembuat 2", "student_id": "87654321", "university": "Universitas Gadjah Mada", "major": "Teknik Komputer", "year": "2021", "contribution": "Pengembang Algoritma dan Data Kota", "photo": None}
    ]

# Fungsi untuk save profiles ke file
def save_profiles(profiles):
    data = []
    for profile in profiles:
        p = profile.copy()
        if p["photo"]:
            p["photo"] = encode_image(p["photo"])
        data.append(p)
    with open("profiles.json", "w") as f:
        json.dump(data, f)

# Custom CSS untuk tema manhwa dark fantasy UI dengan sistem aura dan glow
st.markdown("""
<style>
    body {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #e94560;
        font-family: 'Courier New', monospace;
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
    .system-panel {
        background: rgba(22, 33, 62, 0.9);
        border: 2px solid #0f3460;
        border-radius: 15px;
        box-shadow: 0 0 20px #e94560, inset 0 0 10px rgba(233, 69, 96, 0.3);
        padding: 20px;
        margin: 20px 0;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { box-shadow: 0 0 20px #e94560; }
        to { box-shadow: 0 0 30px #e94560, 0 0 40px #0f3460; }
    }
    .stButton>button {
        background: linear-gradient(45deg, #16213e, #0f3460);
        color: #e94560;
        border: 2px solid #0f3460;
        border-radius: 10px;
        box-shadow: 0 0 10px #0f3460;
        transition: all 0.4s ease;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px #e94560, 0 0 35px #0f3460;
        transform: scale(1.1);
        background: linear-gradient(45deg, #0f3460, #16213e);
    }
    .stButton>button:active {
        box-shadow: 0 0 40px #e94560;
        transform: scale(0.95);
    }
    .stTextInput>input, .stSelectbox>select, .stTextArea>textarea {
        background: rgba(22, 33, 62, 0.8);
        color: #e94560;
        border: 1px solid #0f3460;
        border-radius: 8px;
        box-shadow: inset 0 0 5px rgba(233, 69, 96, 0.2);
        transition: all 0.3s ease;
    }
    .stTextInput>input:focus, .stSelectbox>select:focus, .stTextArea>textarea:focus {
        box-shadow: 0 0 10px #e94560, inset 0 0 10px rgba(233, 69, 96, 0.3);
        border-color: #e94560;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #e94560;
        text-shadow: 0 0 10px #0f3460, 0 0 20px #e94560;
        font-weight: bold;
        text-align: center;
        animation: pulse 3s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { text-shadow: 0 0 10px #0f3460, 0 0 20px #e94560; }
        50% { text-shadow: 0 0 15px #0f3460, 0 0 30px #e94560; }
    }
    .aura-cursor {
        cursor: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8Y2lyY2xlIGN4PSIxNiIgY3k9IjE2IiByPSIxNSIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZTk0NTYwIiBzdHJva2Utd2lkdGg9IjIiLz4KICA8Y2lyY2xlIGN4PSIxNiIgY3k9IjE2IiByPSI1IiBmaWxsPSIjZTk0NTYwIi8+Cjwvc3ZnPg=='), auto;
    }
    .fade-in {
        animation: fadeIn 1.5s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .sidebar .sidebar-content {
        background: rgba(22, 33, 62, 0.9);
        border-right: 2px solid #0f3460;
        box-shadow: inset 0 0 10px rgba(233, 69, 96, 0.2);
    }
    .stDataFrame {
        background: rgba(22, 33, 62, 0.8);
        border: 1px solid #0f3460;
        border-radius: 10px;
        box-shadow: 0 0 10px #e94560;
    }
</style>
""", unsafe_allow_html=True)

# Data Kota (koordinat GPS perkiraan; contoh untuk beberapa kota per provinsi)
cities_data = {
    "Banten": {
        "Serang": (-6.1200, 106.1500),
        "Tangerang": (-6.1781, 106.6319),
        "Cilegon": (-6.0167, 106.0500),
        "Tangerang Selatan": (-6.2931, 106.7133)
    },
    "Jawa Barat": {
        "Bandung": (-6.9175, 107.6191),
        "Bogor": (-6.5950, 106.8167),
        "Bekasi": (-6.2349, 106.9896),
        "Depok": (-6.4025, 106.7942)
    },
    "Jawa Tengah": {
        "Semarang": (-6.9667, 110.4167),
        "Solo": (-7.5667, 110.8167),
        "Yogyakarta": (-7.7956, 110.3695),
        "Magelang": (-7.4706, 110.2178)
    },
    "Yogyakarta": {
        "Yogyakarta": (-7.7956, 110.3695),
        "Sleman": (-7.7167, 110.3667),
        "Bantul": (-7.8833, 110.3333),
        "Gunungkidul": (-7.9667, 110.6167)
    },
    "Jawa Timur": {
        "Surabaya": (-7.2575, 112.7521),
        "Malang": (-7.9667, 112.6333),
        "Kediri": (-7.8167, 112.0167),
        "Madiun": (-7.6167, 111.5167)
    },
    "DKI Jakarta": {
        "Jakarta Pusat": (-6.2088, 106.8456),
        "Jakarta Utara": (-6.1333, 106.8167),
        "Jakarta Barat": (-6.1616, 106.7264),
        "Jakarta Selatan": (-6.2615, 106.8106),
        "Jakarta Timur": (-6.2115, 106.8452)
    }
}

# Fungsi untuk membuat graph
def create_graph(province):
    G = nx.Graph()
    cities = cities_data.get(province, {})
    for city, coord in cities.items():
        G.add_node(city, pos=coord)
    for i, (city1, coord1) in enumerate(cities.items()):
        for city2, coord2 in list(cities.items())[i+1:]:
            dist = geodesic(coord1, coord2).km
            G.add_edge(city1, city2, weight=dist)
    return G

# Fungsi untuk shortest path dengan Dijkstra
def shortest_path(G, start, end):
    try:
        path = nx.shortest_path(G, source=start, target=end, weight='weight')
        length = nx.shortest_path_length(G, source=start, target=end, weight='weight')
        return path, length
    except nx.NetworkXNoPath:
        return None, None

# Fungsi untuk visualisasi peta
def create_map(G, path=None, zoom_city=None):
    m = folium.Map(location=[-7.0, 110.0], zoom_start=8, tiles='CartoDB dark_matter')
    for node, data in G.nodes(data=True):
        folium.Marker(location=data['pos'], popup=node, icon=folium.Icon(color='blue')).add_to(m)
    if path:
        for i in range(len(path)-1):
            coord1 = G.nodes[path[i]]['pos']
            coord2 = G.nodes[path[i+1]]['pos']
            folium.PolyLine([coord1, coord2], color='red', weight=5).add_to(m)
        if zoom_city:
            m.location = G.nodes[zoom_city]['pos']
            m.zoom_start = 12
    return m

# Load profiles dari file
if 'profiles' not in st.session_state:
    st.session_state.profiles = load_profiles()

# Navigasi (ditambahkan halaman baru tanpa mengubah yang lama)
page = st.sidebar.selectbox("Navigasi", ["Dashboard", "Profil Tim", "Matrix Applications", "Map & Graph System"])

if page == "Dashboard":
    st.markdown('<div class="system-panel fade-in"><h1>Map System - Pulau Jawa</h1></div>', unsafe_allow_html=True)
    st.write("Selamat datang di sistem peta interaktif dengan Graph Theory. Pilih halaman untuk melanjutkan.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Profil Tim", key="profil_btn"):
            st.session_state.page = "Profil Tim"
    with col2:
        if st.button("Map & Graph System", key="map_btn"):
            st.session_state.page = "Map & Graph System"

elif page == "Profil Tim":
    st.markdown('<div class="system-panel fade-in"><h2>👤 Profil Tim</h2></div>', unsafe_allow_html=True)
    for i, profile in enumerate(st.session_state.profiles):
        st.subheader(f"Profil {i+1}")
        col1, col2 = st.columns([1, 3])
        with col1:
            # Tampilkan foto dari session state jika ada
            if profile["photo"]:
                st.image(profile["photo"], width=100)
                # Tombol hapus foto
                if st.button(f"Hapus Foto {i+1}", key=f"delete_{i}"):
                    st.session_state.profiles[i]["photo"] = None
                    save_profiles(st.session_state.profiles)  # Save setelah hapus
                    st.rerun()  # Rerun untuk refresh tampilan
            # File uploader selalu muncul
            uploaded_file = st.file_uploader(f"Upload Foto {i+1}", type=["jpg", "png"], key=f"upload_{i}")
            if uploaded_file:
                # Buka gambar dan simpan ke session state
                image = Image.open(uploaded_file)
                st.session_state.profiles[i]["photo"] = image
                # Tampilkan gambar langsung setelah upload
                st.image(image, width=100)
                save_profiles(st.session_state.profiles)  # Save setelah upload
        with col2:
            st.session_state.profiles[i]["name"] = st.text_input("Nama", profile["name"], key=f"name_{i}")
            st.session_state.profiles[i]["student_id"] = st.text_input("Student ID", profile["student_id"], key=f"id_{i}")
            st.session_state.profiles[i]["university"] = st.text_input("Universitas", profile["university"], key=f"uni_{i}")
            st.session_state.profiles[i]["major"] = st.text_input("Jurusan", profile["major"], key=f"major_{i}")
            st.session_state.profiles[i]["year"] = st.text_input("Angkatan", profile["year"], key=f"year_{i}")
            st.session_state.profiles[i]["contribution"] = st.text_area("Deskripsi Kontribusi", profile["contribution"], key=f"contrib_{i}")
    # Save profiles setelah semua input (untuk text changes)
    save_profiles(st.session_state.profiles)

elif page == "Matrix Applications":
    st.markdown('<div class="system-panel fade-in"><h2>📊 Matrix Applications</h2></div>', unsafe_allow_html=True)
    province = st.selectbox("Pilih Provinsi untuk Graph", list(cities_data.keys()))
    if province:
        G = create_graph(province)
        st.write(f"Graph untuk {province} dibuat dengan {len(G.nodes)} kota.")
        
        # Graph Visualization
        st.subheader("Graph Visualization")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_facecolor('#1a1a2e')
        fig.patch.set_facecolor('#1a1a2e')
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='#16213e', edge_color='#e94560', ax=ax, font_color='#e94560')
        st.pyplot(fig)
        
        # Degree tiap vertex
        st.subheader("Degree Tiap Vertex")
        degrees = dict(G.degree())
        for node, deg in degrees.items():
            st.write(f"{node}: Degree {deg}")
        
        # Adjacency Matrix
        st.subheader("Adjacency Matrix")
        adj_matrix = nx.adjacency_matrix(G).todense()
        st.dataframe(adj_matrix)

elif page == "Map & Graph System":
    st.markdown('<div class="system-panel fade-in"><h2>🗺️ Map & Graph System</h2></div>', unsafe_allow_html=True)
    province = st.selectbox("Pilih Provinsi", list(cities_data.keys()))
    if province:
        G = create_graph(province)
        st.write(f"Graph untuk {province} dibuat dengan {len(G.nodes)} kota.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            start_city = st.selectbox("Kota Awal", list(G.nodes), key="start")
        with col2:
            end_city = st.selectbox("Kota Tujuan", list(G.nodes), key="end")
        
        if start_city and end_city and start_city != end_city:
            path, length = shortest_path(G, start_city, end_city)
            if path:
                st.success(f"Jalur Terpendek: {' -> '.join(path)} | Jarak: {length:.2f} km")
                m = create_map(G, path, end_city)
            else:
                st.error("Tidak ada jalur tersedia.")
                m = create_map(G)
        else:
            m = create_map(G)
        
        st_folium(m, width=700, height=500)
    
    # Pencarian Kota
    st.subheader("🔍 Pencarian Kota")
    search_input = st.text_input("Masukkan nama kota", "")
    st.markdown("❓ Klik ikon untuk panduan: Masukkan nama kota yang tepat (case-sensitive).")
    if search_input:
        found = any(search_input in city for cities in cities_data.values() for city in cities)
        if not found:
            st.error("Kota tidak ditemukan. Periksa ejaan!", icon="⚠️")

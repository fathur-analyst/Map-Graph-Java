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
import pandas as pd
import json
import os

# -------------------------
# Helper: encode/decode image
# -------------------------
def encode_image(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def decode_image(encoded_str: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(encoded_str)))

# -------------------------
# Load / Save profiles
# -------------------------
def load_profiles():
    if os.path.exists("profiles.json"):
        with open("profiles.json", "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return []
            # decode photos if ada
            for profile in data:
                if profile.get("photo"):
                    try:
                        profile["photo"] = decode_image(profile["photo"])
                    except Exception:
                        profile["photo"] = None
            return data
    # Default example profiles
    return [
        {"name": "Pembuat 1", "student_id": "12345678", "university": "Universitas Indonesia", "major": "Informatika", "year": "2020", "contribution": "Pengembang UI dan Graph Theory", "photo": None},
        {"name": "Pembuat 2", "student_id": "87654321", "university": "Universitas Gadjah Mada", "major": "Teknik Komputer", "year": "2021", "contribution": "Pengembang Algoritma dan Data Kota", "photo": None}
    ]

def save_profiles(profiles):
    data = []
    for profile in profiles:
        p = profile.copy()
        if p.get("photo") and isinstance(p["photo"], Image.Image):
            try:
                p["photo"] = encode_image(p["photo"])
            except Exception:
                p["photo"] = None
        else:
            p["photo"] = None
        data.append(p)
    with open("profiles.json", "w") as f:
        json.dump(data, f, indent=2)
# -------------------------
# Custom CSS theme
# -------------------------
st.markdown("""
<style>
    body {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #e94560;
        font-family: 'Courier New', monospace;
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
        transform: scale(1.05);
    }
    .stTextInput>input, .stSelectbox>select, .stTextArea>textarea, .stNumberInput>input {
        background: rgba(22, 33, 62, 0.8);
        color: #e94560;
        border: 1px solid #0f3460;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Data kota (koordinat)
# -------------------------
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

# -------------------------
# Graph builder & algorithms
# -------------------------
def create_graph(province: str) -> nx.Graph:
    G = nx.Graph()
    cities = cities_data.get(province, {})
    for city, coord in cities.items():
        G.add_node(city, pos=coord)
    # add weighted edges (complete graph among cities in province)
    city_items = list(cities.items())
    for i in range(len(city_items)):
        city1, coord1 = city_items[i]
        for j in range(i+1, len(city_items)):
            city2, coord2 = city_items[j]
            try:
                dist = geodesic(coord1, coord2).km
            except Exception:
                dist = float(np.linalg.norm(np.array(coord1) - np.array(coord2)))
            G.add_edge(city1, city2, weight=dist)
    return G

def shortest_path(G: nx.Graph, start: str, end: str):
    try:
        path = nx.shortest_path(G, source=start, target=end, weight='weight')
        length = nx.shortest_path_length(G, source=start, target=end, weight='weight')
        return path, length
    except nx.NetworkXNoPath:
        return None, None
    except Exception:
        return None, None

# -------------------------
# Folium map
# -------------------------
def create_map(G: nx.Graph, path=None, zoom_city=None, default_location=[-7.0, 110.0], default_zoom=7):
    # choose starting center: zoom_city if provided else default center
    if zoom_city and zoom_city in G.nodes:
        center = list(G.nodes[zoom_city]['pos'])
        zoom = 11
    else:
        center = default_location
        zoom = default_zoom

    m = folium.Map(location=center, zoom_start=zoom, tiles='CartoDB dark_matter')
    # markers
    for node, data in G.nodes(data=True):
        folium.Marker(location=data['pos'], popup=node, icon=folium.Icon(color='blue')).add_to(m)
    # all edges in blue (menampilkan garis saling terhubung antar kota saat provinsi dipilih)
    for u, v in G.edges():
        coord1 = G.nodes[u]['pos']
        coord2 = G.nodes[v]['pos']
        folium.PolyLine([coord1, coord2], color='blue', weight=3, opacity=0.7).add_to(m)
    # path lines in red (highlight untuk path terpendek saat memilih dua kota)
    if path and len(path) >= 2:
        for i in range(len(path)-1):
            coord1 = G.nodes[path[i]]['pos']
            coord2 = G.nodes[path[i+1]]['pos']
            folium.PolyLine([coord1, coord2], color='red', weight=5).add_to(m)
    return m
    
# -------------------------
# Session state: profiles
# -------------------------
if 'profiles' not in st.session_state:
    st.session_state.profiles = load_profiles()

# -------------------------
# Navigation
# -------------------------
page = st.sidebar.selectbox("Navigasi", ["Dashboard", "Profil Tim", "Graph Visualization", "Map & Graph System"])

if page == "Dashboard":
    st.markdown('<div class="system-panel"><h1>Map System - Pulau Jawa</h1></div>', unsafe_allow_html=True)
    st.write("Selamat datang di sistem peta interaktif dengan Graph Theory.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Profil Tim"):
            st.experimental_rerun()  # biarkan selectbox handle navigation
    with col2:
        if st.button("Map & Graph System"):
            st.experimental_rerun()

elif page == "Profil Tim":
    st.markdown('<div class="system-panel"><h2>👤 Profil Tim</h2></div>', unsafe_allow_html=True)
    for i, profile in enumerate(st.session_state.profiles):
        st.subheader(f"Profil {i+1}")
        col1, col2 = st.columns([1, 3])
        with col1:
            # Tampilkan foto dari session state jika ada
            if profile["photo"]:
                st.image(profile["photo"], width=100)
                # Tombol hapus foto hanya jika profil belum final (nama kosong)
                if not profile.get("name"):
                    if st.button(f"Hapus Foto {i+1}", key=f"delete_{i}"):
                        st.session_state.profiles[i]["photo"] = None
                        save_profiles(st.session_state.profiles)
                        st.experimental_rerun()
            # File uploader hanya jika profil belum final (nama kosong)
            if not profile.get("name"):
                uploaded_file = st.file_uploader(f"Upload Foto {i+1}", type=["jpg", "png"], key=f"upload_{i}")
                if uploaded_file:
                    # Buka gambar dan simpan ke session state
                    try:
                        image = Image.open(uploaded_file).convert("RGBA")
                    except Exception:
                        image = Image.open(uploaded_file)
                    st.session_state.profiles[i]["photo"] = image
                    # Tampilkan gambar langsung setelah upload
                    st.image(image, width=100)
                    save_profiles(st.session_state.profiles)
        with col2:
            # Input fields disabled jika nama sudah diisi (profil final)
            disabled = bool(profile.get("name"))
            st.session_state.profiles[i]["name"] = st.text_input("Nama", profile.get("name", ""), key=f"name_{i}", disabled=disabled)
            st.session_state.profiles[i]["student_id"] = st.text_input("Student ID", profile.get("student_id", ""), key=f"id_{i}", disabled=disabled)
            st.session_state.profiles[i]["university"] = st.text_input("Universitas", profile.get("university", ""), key=f"uni_{i}", disabled=disabled)
            st.session_state.profiles[i]["major"] = st.text_input("Jurusan", profile.get("major", ""), key=f"major_{i}", disabled=disabled)
            st.session_state.profiles[i]["year"] = st.text_input("Angkatan", profile.get("year", ""), key=f"year_{i}", disabled=disabled)
            st.session_state.profiles[i]["contribution"] = st.text_area("Deskripsi Kontribusi", profile.get("contribution", ""), key=f"contrib_{i}", disabled=disabled)
    # Save profiles setelah semua input (untuk text changes)
    save_profiles(st.session_state.profiles)

elif page == "Graph Visualization":
    st.markdown('<div class="system-panel"><h2>📊 Graph Visualization</h2></div>', unsafe_allow_html=True)

    
    # Input Kontrol
    st.subheader("1. ⚙️ Input Kontrol")
    st.write("Anda dapat menentukan parameter dasar graf:")
    num_nodes = st.number_input("Enter number of nodes", min_value=1, max_value=10, value=5, step=1)
    num_edges = st.number_input("Enter number of edges", min_value=0, max_value=num_nodes*(num_nodes-1)//2, value=3, step=1)
    
    # Generate random graph
    if num_nodes > 0:
        G = nx.gnm_random_graph(num_nodes, num_edges)
        # Relabel nodes to 1-based
        mapping = {i: i+1 for i in range(num_nodes)}
        G = nx.relabel_nodes(G, mapping)
        
        # Visualisasi Graf
        st.subheader("2. 🌐 Visualisasi Graf")
        st.write("Terdapat area tampilan graf di mana struktur graf digambarkan secara visual. Simpul-simpul diberi nomor dan garis-garis menunjukkan koneksi di antaranya.")
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_size=300, node_color='#16213e', edge_color='#e94560', ax=ax, font_color='#e94560')
        st.pyplot(fig)
        
        # Degree of Each Node
        st.subheader("3. 📝 Hasil Analisis: Degree of Each Node (Derajat Setiap Simpul)")
        st.write("Ini menunjukkan analisis dasar dari topologi graf:")
        st.markdown("- Degree (derajat) dari sebuah simpul adalah jumlah tepian yang terhubung langsung dengannya.")
        degrees = dict(G.degree())
        for node, deg in degrees.items():
            st.markdown(f"- Node {node}: {deg}")
        
        # Adjacency Matrix
        st.subheader("4. 🧮 Hasil Analisis: Adjacency Matrix (Matriks Ketetanggaan)")
        st.write("Matriks ini adalah representasi matematis dari graf yang menunjukkan koneksi antar simpul:")
        st.markdown(f"- Ini adalah matriks berukuran $N \\times N$ (di mana $N$ adalah jumlah simpul, yaitu ${num_nodes} \\times {num_nodes}$).")
        st.markdown("- Nilai 1 di baris $i$ dan kolom $j$ berarti ada tepian antara simpul $i$ dan simpul $j$.")
        st.markdown("- Nilai 0 berarti tidak ada tepian antara simpul tersebut.")
        st.markdown("- Contoh: Nilai 1 di Baris 1, Kolom 2 menunjukkan bahwa Node 1 dan Node 2 terhubung. Nilai 0 di Baris 1, Kolom 3 menunjukkan bahwa Node 1 dan Node 3 tidak terhubung.")
        st.markdown("- Karena graf ini tampak tidak berarah (undirected), matriksnya simetris (misalnya, Baris 2, Kolom 4 = 1, dan Baris 4, Kolom 2 juga = 1).")
        adj_matrix = nx.adjacency_matrix(G).todense()
        st.dataframe(adj_matrix)

elif page == "Map & Graph System":
    st.markdown('<div class="system-panel"><h2>🗺️ Map & Graph System</h2></div>', unsafe_allow_html=True)
    province = st.selectbox("Pilih Provinsi", list(cities_data.keys()))
    if province:
        G = create_graph(province)
        st.write(f"Graph untuk {province} dibuat dengan {len(G.nodes)} kota.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            start_city = st.selectbox("Kota Awal", list(G.nodes), key="start")
        with col2:
            end_city = st.selectbox("Kota Tujuan", list(G.nodes), key="end")
     
             # Pencarian Kota (case-insensitive)
        st.subheader("🔍 Pencarian Kota")
        search_input = st.text_input("Masukkan nama kota (bisa partial, case-insensitive)", "")
        found_matches = []
        if search_input:
            q = search_input.strip().lower()
            for prov, cities in cities_data.items():
                for city, coord in cities.items():
                    if q in city.lower():
                        found_matches.append((prov, city, coord))
            if not found_matches:
                st.error("Kota tidak ditemukan. Periksa ejaan!", icon="⚠️")
            else:
                st.success(f"Ditemukan {len(found_matches)} hasil:")
                for idx, (prov, city, coord) in enumerate(found_matches, start=1):
                    st.write(f"{idx}. {city} — {prov} ({coord[0]:.4f}, {coord[1]:.4f})")
                # Pilih hasil untuk di-zoom
                sel = st.selectbox("Pilih hasil untuk zoom ke peta", ["(tidak ada pilihan)"] + [f"{c} — {p}" for p, c, _ in [(x[0], x[1], x[2]) for x in found_matches]])
                zoom_city = None
                if sel != "(tidak ada pilihan)":
                    # sel string format "City — Province"
                    city_name = sel.split(" — ")[0].strip()
                    if city_name in G.nodes:
                        zoom_city = city_name
                    else:
                        # city from different province (not in current G)
                        # find the coord and create a temporary single-node map centering there
                        match = next((m for m in found_matches if m[1] == city_name), None)
                        if match:
                            # create a tiny map centered on this external city
                            m_temp = folium.Map(location=list(match[2]), zoom_start=11, tiles='CartoDB dark_matter')
                            folium.Marker(location=match[2], popup=city_name).add_to(m_temp)
                            st_folium(m_temp, width=700, height=400)
                            zoom_city = None  # we already displayed a focused map
        else:
            zoom_city = None

        # compute path only if start and end are distinct
        if start_city and end_city:
            if start_city == end_city:
                st.warning("Kota awal dan tujuan sama — pilih kota berbeda untuk menghitung jalur.")
                path = None
                length = None
            else:
                path, length = shortest_path(G, start_city, end_city)
                if path:
                    st.success(f"Jalur Terpendek: {' -> '.join(path)} | Jarak: {length:.2f} km")
                else:
                    st.error("Tidak ada jalur tersedia.")
        else:
            path = None
            length = None

        # buat peta akhir (zoom ke path/end/selected city bila ada)
        # jika zoom_city dari pencarian dan ada di graph, gunakan itu; jika tidak, gunakan end_city jika ada
        map_zoom_target = zoom_city if (zoom_city and zoom_city in G.nodes) else (end_city if end_city in G.nodes else None)
        m = create_map(G, path=path, zoom_city=map_zoom_target)
        st_folium(m, width=700, height=500)

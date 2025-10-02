# 🚀 IPTU Checker: Satellite-Based Land Measurement Analyzer with AI

## 📌 Objective

**IPTU Checker** is a system that utilizes **satellite imagery, AI, and geospatial analysis** to compare the actual land size with the registered data provided by property owners. The goal is to help **municipalities** and **tax authorities** ensure **fair and accurate property tax (IPTU) assessments**.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| 🛰️ **Google Earth Engine / Sentinel-2 / Landsat-8** | Satellite image collection |
| 📡 **Google Maps API / OpenStreetMap** | Address validation and georeferencing |
| 🧠 **Computer Vision (OpenCV, TensorFlow, YOLO)** | Land segmentation and construction detection |
| 🗺️ **GeoPandas & Shapely** | Geospatial analysis and polygon comparison |
| 💾 **BigQuery or PostgreSQL + PostGIS** | Database for data storage and insights |
| 📊 **Streamlit / Dash** | Interactive dashboard for analysis |

---

## 🔍 How It Works?

### **1️⃣ Data Collection**
📍 Retrieves satellite images of the city.  
📂 Fetches cadastral data from the municipality (owner-reported land size).  
🗺️ Uses Google Maps/OpenStreetMap APIs to georeference land plots.  

### **2️⃣ Image Processing**
🖼️ Uses OpenCV + YOLO to identify land and building boundaries.  
📏 Calculates the actual area of the land through image segmentation.  

### **3️⃣ Geospatial Analysis**
📐 Compares actual construction polygons with registered information.  
📊 Detects discrepancies in reported land size.  

### **4️⃣ Interactive Interface**
🖥️ Displays results via **Streamlit/Dash**.  
📋 Allows municipalities and auditors to analyze data visually.  
📝 Provides reports on IPTU discrepancies.  

---

## ⚙️ Installation & Setup

### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/yourusername/IPTU-Checker.git
cd IPTU-Checker
```

### **2️⃣ Create a Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4️⃣ Configure Google Maps API**
- Go to **Google Cloud Console**.
- Enable the **Google Maps API**.
- Generate an **API key** and add it to the `config/api_keys.py` file:
```python
API_KEY = "YOUR_API_KEY_HERE"
```

### **5️⃣ Set Up the Database**
- If using **PostgreSQL + PostGIS**, create a database:
```sql
CREATE DATABASE iptu_db;
CREATE EXTENSION postgis;
```
- Edit `src/database.py` and update the credentials:
```python
DB_URL = "postgresql://user:password@localhost:5432/iptu_db"
```

---

## 🚀 Running the Project

### **1️⃣ Data Collection & Processing**
```bash
python src/data_processing.py
```

### **2️⃣ Image Processing**
```bash
python src/image_analysis.py
```

### **3️⃣ Geospatial Analysis**
```bash
python src/geospatial_analysis.py
```

### **4️⃣ Web Interface (Dashboard)**
```bash
streamlit run src/app.py
```
Access in your browser: **`http://localhost:8501`**

### **5️⃣ REST API (Optional)**
```bash
python src/api.py
```
API Documentation: **`http://localhost:8000/docs`**

---

## 📊 Sample Output

| Address | Registered Area (m²) | Actual Area (m²) | Difference (%) |
|----------|---------------------|-----------------|---------------|
| Avenida Paulista, SP | 100 | 120 | 20% |
| Rua das Flores, RJ | 200 | 180 | -10% |

📌 **If the actual area is larger than the registered area**, there may be **IPTU tax evasion**.  
📌 **If the actual area is smaller**, the owner may be **overpaying IPTU**.  

---

## ✅ Available Features
✅ **REST API** - FastAPI with endpoints for municipal integration (`/docs`)  
✅ **Interactive Maps** - Clickable maps with property status visualization  

## 🛠️ Future Improvements
⚪ Implement an **automated AI bot** to detect suspicious patterns.  

---

## 📜 License
This project is licensed under the **MIT License** – Feel free to contribute and adapt! 🎯


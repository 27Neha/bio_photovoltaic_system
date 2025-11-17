# ⚡ Biophotonix: Bio-Photovoltaic Energy System

## Harnessing Nature’s Energy 🌱

---

## 📌 Project Overview

**Biophotonix** is a proof-of-concept bio-photovoltaic energy system designed to generate **micro-level electricity** using **fruit juice electrolytes** as a sustainable, low-cost replacement for traditional silicon panels.

The core innovation lies in its **Weather-Intelligent Engine**, which uses real-time weather data from external APIs to analyze the user’s local climate and recommend the optimal fruit electrolyte based on factors like temperature, humidity, cloud cover, UV index, and cost efficiency.

This project demonstrates a fusion of biology and technology to create sustainable, accessible, and data-driven micro-energy solutions.

---

## 🎯 Key Features

| Feature | Description |
| :--- | :--- |
| **🌦️ Weather-Intelligent Engine** | Fetches live weather data using **OpenWeatherMap** to inform recommendations. |
| **🍊 Fruit Electrolyte Recommendation** | Suggests the fruit with the highest suitability score based on chemical properties vs. climate. |
| **⚡ Bio-Solar Power Output Estimation** | Calculates estimated energy output using fruit **pH**, **acidity**, and **conductivity** parameters. |
| **💰 Cost & Efficiency Analysis** | Provides fruit **cost per kg** and estimated system operating cost for economic feasibility. |
| **🔌 Compatible Device Suggestions** | Identifies small, low-power devices the system is capable of running (e.g., LED lights, small sensors). |
| **💻 Modern 3D UI** | Features a clean, interactive design with smooth animations and **glassmorphism** accents for an intuitive user experience. |

---

## 🧪 How It Works (System Flow)

1.  **Input:** User enters city name (or enables auto-location).
2.  **Data Fetch:** System fetches real-time climate data (temperature, humidity, etc.).
3.  **Analysis:** Weather data is compared with the JSON-based chemical properties of various fruits.
4.  **Scoring:** A fruit scoring algorithm ranks fruits based on their chemical suitability for the current climate conditions.
5.  **Recommendation Display:** Top recommended fruits are displayed with detailed metrics:
    * pH level & acidity
    * Cost per kg
    * Climate specialization (e.g., best in high humidity)
    * Overall efficiency score
6.  **Energy Calculation:** User proceeds to the **Energy Calculator**, which displays:
    * Detailed weather breakdown
    * Selected fruit configuration
    * Estimated power output
    * Installation requirements
    * Compatible devices

---

## 🧩 Tech Stack

### Frontend
* **HTML5**
* **CSS3** (Custom design with **Glassmorphism** accents)
* **Vanilla JavaScript** (DOM manipulation and API interaction)

### Backend
* **Python** (**Flask** framework for API routing and business logic)
* **Weather API Integration**
* **JSON**-based fruit data (chemical and cost profiles)

### External API
* **🌤️ OpenWeatherMap API**

---

## ⚙️ Installation & Setup

### Prerequisites
* Python 3.x
* `pip` (Python package installer)

### Steps

1.  **Clone the Repository**

    ```bash
    git clone [https://github.com/your-username/BIO_PHOTO_VOLTAIC_SYSTEM.git](https://github.com/your-username/BIO_PHOTO_VOLTAIC_SYSTEM.git)
    cd BIO_PHOTO_VOLTAIC_SYSTEM
    ```

2.  **Install Dependencies (Backend)**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Add your OpenWeatherMap API key**

    Locate or create `app.py` or a dedicated config file and securely insert your API key:

    ```python
    API_KEYS = { "openweathermap": "YOUR_API_KEY" }
    ```

4.  **Run the Backend Server**

    ```bash
    python app.py
    ```

5.  **Access the Frontend**

    Open `templates/index.html` in your web browser.

---

## 🔍 Project Structure
├── templates/
│   ├── index.html          # Welcome/Main screen
│   ├── calculator.html     # Energy Output Calculator screen
│   └── recommendations.html# Fruit Recommendation results screen
├── scripts/
│   ├── check_provider.py   # Utility script to check API provider status
│   └── test_fetch_openweather.py # Unit test for weather API fetching
├── app.py                  # Main Flask backend application file
├── static/
│   ├── css/                # Stylesheets for the UI (e.g., glassmorphism)
│   └── js/                 # Frontend JavaScript logic
└── README.md               # Project documentation and setup guide
---

## 💡 Use Cases

* **Rural Energy Access:** Providing a simple, low-cost way to charge small devices in off-grid locations.
* **Low-cost Micro-Power Generation:** Accessible energy source for small, local needs.
* **Educational Demonstration:** A highly engaging science and engineering project to demonstrate bio-energy principles.
* **Eco-friendly Science Projects:** Promoting sustainable engineering concepts.
* **Disaster Relief:** Simple, quickly deployable micro-power systems for essential devices.

---

## 🚧 Current Limitations

* **Low Voltage Output:** Fruit-based cells inherently generate low voltage (**micro-power**).
* **Freshness Dependence:** Output efficiency is highly dependent on the **freshness** and chemical composition of the fruit.
* **No ML/DL Integration:** No Machine Learning or Deep Learning algorithms were implemented due to time constraints (using rule-based scoring instead).
* **Weather Variability:** Efficiency scores can fluctuate significantly with rapid weather changes.

---

## 🔮 Future Enhancements

* **Machine Learning Integration:** Implement ML models for smarter, predictive fruit electrolyte recommendations.
* **Database Storage:** Integrate a database for user history, analytics, and performance logging.
* **Real-time Sensing:** Introduce support for real-time voltage and current sensors to connect with physical prototypes.
* **Expanded Fruit Dataset:** Systematically expand the fruit dataset with comprehensive conductivity and detailed chemical profiles.
* **Full Deployment:** Deploy as a fully hosted web application with a robust API gateway.

---

## 🙌 Team Members

* **Neha Mahajan** – Team Leader
* **Tejas Bhavsar** – 
* **Mentor:** Sagar Yadhav
* **Institute:** Dr. D. Y. Patil School of Science & Technology

---

## 🏁 Conclusion

The Biophotonix project successfully demonstrates how natural fruit electrolytes, when combined with modern data-driven technology and real-time weather analysis, can serve as a sustainable and accessible alternative for **micro-level clean energy generation**.

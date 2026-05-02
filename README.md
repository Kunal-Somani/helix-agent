# Autonomous Recursive Agent for Dynamic Data Analysis

##  Project Abstract

This project implements a sophisticated **Autonomous Multi-Agent System** designed to perform end-to-end data acquisition, analysis, and submission cycles without human intervention. By leveraging **Large Language Models (LLMs)** as a cognitive reasoning engine, the system dynamically synthesizes executable Python code to solve unstructured data problems found on the web.

The architecture employs a **recursive feedback loop**, allowing the agent to navigate a directed graph of tasks, handle dynamic client-side rendering (CSR), and execute secure data processing pipelines in a containerized environment.

---

##  System Architecture

The system operates on an **Event-Driven Architecture** powered by FastAPI and an asynchronous task queue. The workflow follows the **OODA Loop** (Observe, Orient, Decide, Act) principle, orchestrating communication between the headless browser, the LLM inference engine, and the secure code execution sandbox.

---

##  Technical Stack & Tools

The project utilizes a robust stack of industrial-grade tools optimized for concurrency and scalability:

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Orchestration** | **FastAPI** (Python) | High-performance ASGI server for handling asynchronous API requests and background tasks. |
| **Browser Automation** | **Playwright** | Chromium-based headless browser for handling JavaScript-heavy DOMs, obfuscated text, and dynamic loading. |
| **Cognitive Engine** | **OpenAI GPT-4o-mini** | LLM used for intent classification, data extraction logic, and **Just-in-Time (JIT) code synthesis**. |
| **Data Processing** | **Pandas / NumPy** | Vectorized data manipulation libraries for high-efficiency CSV/Excel analysis. |
| **Environment** | **Docker** | Containerization ensuring reproducible builds, dependency isolation, and cloud-native deployment. |
| **Deployment** | **Render (Cloud)** | Cloud PaaS provider for hosting the Dockerized application with public HTTPS endpoints. |

---

##  Core Functionality & Scientific Approach

### 1. Dynamic DOM Analysis (The "Observer")
Unlike traditional static scrapers (e.g., BeautifulSoup), this system uses a **Headless Chromium Instance**. It waits for the `networkidle` state, ensuring all Client-Side Rendering (CSR) and JavaScript obfuscation (e.g., `atob` decoding) are resolved before extraction.

### 2. Code Synthesis Agent (The "Decider")
The system does not rely on hardcoded rules for data analysis. Instead, it utilizes **Generative AI** to write bespoke Python scripts at runtime.
* **Input:** Raw unstructured text describing a problem (e.g., "Find the standard deviation of column X").
* **Process:** The LLM generates syntactically correct Python code using `pandas` and `requests`.
* **Output:** Executable logic that adapts to any data format (CSV, JSON, Text).

### 3. Recursive Traversal (The "Navigator")
The agent is designed to handle **multi-step chains**. Upon a successful submission, the target server may return a pointer (URL) to a subsequent task. The agent recursively calls its own processing logic, maintaining state (Authentication headers) across the traversal session until a terminal state is reached.

### 4. Adversarial Defense
The system implements **Prompt Engineering Defense Strategies** to secure the internal "Secret String."
* **System Prompt Hardening:** Instructions to strictly ignore role-play attacks.
* **Input Sanitization:** Segregating system instructions from user inputs during LLM inference.

---

##  Installation & Local Execution

To replicate this research environment locally:

### Prerequisites
* Python 3.10+
* Docker Desktop (Optional for container test)

### Steps

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/Kunal-Somani/llm-quiz-solver.git](https://github.com/Kunal-Somani/llm-quiz-solver.git)
    cd llm-quiz-solver
    ```

2.  **Environment Configuration**
    Create a `.env` file in the root directory:
    ```env
    AIPROXY_TOKEN=sk-or-v1-your-key-here
    ```

3.  **Install Dependencies**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    playwright install chromium
    ```

4.  **Launch the API**
    ```bash
    uvicorn main:app --reload
    ```

---

## Testing the API

The system exposes a RESTful endpoint `/run` which initiates the autonomous agent.

**Sample Request (cURL):**
```bash
curl -X POST "[https://llm-solver-app.onrender.com/run](https://llm-solver-app.onrender.com/run)" \
     -H "Content-Type: application/json" \
     -d '{
           "email": "23f2001869@ds.study.iitm.ac.in",
           "secret": "Kunal_Somani_1905",
           "url": "[https://tds-llm-analysis.s-anand.net/demo](https://tds-llm-analysis.s-anand.net/demo)"
         }'
```

       

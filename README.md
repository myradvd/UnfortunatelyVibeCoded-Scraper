
# CURRENT STATUS

## How to Run Locally

> **Note:** No agent has been deployed yet. This setup is currently for local checks only.

### 1. Navigate to the Backend

```bash
cd backend
````

Moves into the `backend` folder.

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

Creates an isolated Python environment in a new `venv` folder. This keeps the project's packages separate from other Python projects on your system.

### 3. Activate the Virtual Environment

```bash
source venv/bin/activate
```

Activates the virtual environment in the current shell.

After activation, your terminal prompt should show:

```text
(venv)
```

Any packages installed with `pip` will now be installed inside this project's virtual environment.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Installs all packages listed in `requirements.txt`, including:

* Flask
* flask-cors
* requests
* gunicorn

### 5. Start the Backend

```bash
python3 app.py
```

Starts the backend server.

Leave this terminal running. The backend should now be listening on:

```text
http://localhost:5000
```

## Run the Frontend

Open a **second terminal** (e.g. a new WSL tab).

### 6. Navigate to the Frontend

```bash
cd ~/getajob/frontend
```

### 7. Start the Frontend Server

```bash
python3 -m http.server 8000
```

Runs Python's built-in HTTP server and serves the contents of the current folder on port `8000`.

### 8. Open the Application

Open the following URL in your browser:

```text
http://localhost:8000
```

You should now see the UI.

> **Note:** The listings will be empty until the agent sends job listings. This will be implemented in soon

```
```

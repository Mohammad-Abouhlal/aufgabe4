# Basis-Image
FROM python:3.9-slim

# Arbeitsverzeichnis festlegen
WORKDIR /app

# Abhängigkeiten kopieren
COPY requirements.txt .

# Abhängigkeiten installieren
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Port, auf dem die App läuft
EXPOSE 5000

# Befehl zum Starten der Anwendung
CMD ["python", "app.py"]
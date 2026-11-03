# La version de l'image et celle du paquet pip doivent être identiques
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

RUN pip install --no-cache-dir playwright==1.48.0

WORKDIR /app
COPY clicker.py .

CMD ["python", "-u", "clicker.py"]

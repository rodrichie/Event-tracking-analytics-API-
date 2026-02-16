FROM python:3.13-slim-bullseye

RUN pip install --no-cache-dir \
    streamlit==1.41.0 \
    pandas==2.2.3 \
    plotly==5.24.1 \
    psycopg2-binary==2.9.10 \
    requests==2.32.3

WORKDIR /app
COPY app.py .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

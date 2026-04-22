FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home appuser && \
    mkdir -p /data && \
    chown -R appuser:appuser /data /app
USER appuser
EXPOSE 5005
ENV FLASK_ENV=production
ENV DB_NAME=/data/aceest_fitness.db
CMD ["python", "app.py"]
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY run_test.py run_test.sh /app/
RUN chmod +x /app/run_test.sh

ENTRYPOINT ["/app/run_test.sh"]

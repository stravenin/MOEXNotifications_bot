FROM python:3.12

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends wait-for-it && apt-get clean && rm -rf /var/lib/apt/lists/*


EXPOSE 1200

CMD wait-for-it notifications:1200 --timeout=5 -- sh -c 'alembic upgrade head'; wait-for-it notifications:1200 --timeout=5 -- sh -c 'python main.py';
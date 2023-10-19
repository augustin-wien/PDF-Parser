FROM python:3.11
RUN mkdir /app
WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD *.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload"] 
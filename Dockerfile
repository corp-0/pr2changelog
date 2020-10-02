FROM python:3
COPY . /.
CMD ["pip install poetry"]
CMD ["poetry install"]
CMD ["python", "/main.py"]
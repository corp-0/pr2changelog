import os
import json
import requests
from .document import Document
from .change import Change

__version__ = '0.1.0'

os.environ['INPUT_FILE_NAME'] = 'CHANGELOG.md'

try:
    REPO = os.environ['INPUT_REPO']
    TOKEN = os.environ['INPUT_TOKEN']
    PR_NUMBER = os.environ['INPUT_PR_NUMBER']
    CHANGE_TOKEN = os.environ['INPUT_CHANGE_TOKEN']
    FILE_NAME = os.environ['INPUT_FILE_NAME']
except KeyError:
    print("Something is wrong with envs!")
    raise KeyError

r = requests.get(f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}")
data = json.loads(r.text)

document = Document(FILE_NAME)
change = Change(data)
import json


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flatten_json(item):
    texts = []

    def extract(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                extract(v, prefix + f"{k}: ")
        elif isinstance(obj, list):
            for v in obj:
                extract(v, prefix)
        else:
            texts.append(prefix + str(obj))

    extract(item)
    return " ".join(texts)


def load_documents(path):
    data = load_json(path)
    return [flatten_json(item) for item in data]

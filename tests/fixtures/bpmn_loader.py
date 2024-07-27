from pathlib import Path


def load_bpmn(filename):
    with open(Path(__file__).parent / filename, "r") as file:
        return file.read()

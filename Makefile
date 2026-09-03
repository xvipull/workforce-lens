.PHONY: pipeline eda test

pipeline:
	python3 src/pipeline.py

eda: pipeline
	python3 notebooks/eda.py

test:
	python3 -m unittest discover -s tests -v

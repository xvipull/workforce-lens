.PHONY: pipeline advanced eda test

pipeline:
	python3 src/pipeline.py

advanced: pipeline
	python3 src/advanced_analytics.py

eda: pipeline
	python3 notebooks/eda.py

test:
	python3 -m unittest discover -s tests -v

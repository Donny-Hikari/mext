
default: test clean install

install:
	pip install .

clean:
	python setup.py clean --all

test:
	python -m unittest tests.test

readme:
	python -m tools.render_mext README-yaml.mext -o README.yaml
	python -m tools.render_mext README.mext -o README

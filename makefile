
default: test clean install

install:
	pip install .

clean:
	python setup.py clean --all

test:
	python -m unittest tests.test

README: readme_src/*
	python -m mext.scripts.render_mext readme_src/README-yaml.mext -o readme_src/README.yaml
	python -m mext.scripts.render_mext readme_src/README.mext -o README

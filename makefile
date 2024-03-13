
default: test clean install

install:
	pip install .

clean:
	python setup.py clean --all

test:
	python -m unittest tests.test

readme_src/README.yaml: readme_src/README-yaml.yaml readme_src/README-yaml.mext
	python -m mext.scripts.render_mext readme_src/README-yaml.mext -o readme_src/README.yaml

README.md: readme_src/README.yaml readme_src/README.mext readme_src/syntax.mext readme_src/template_language_usage.mext
	python -m mext.scripts.render_mext readme_src/README.mext -o README.md

docs/syntax.md: readme_src/README.yaml readme_src/syntax.mext
	python -m mext.scripts.render_mext readme_src/syntax.mext -o docs/syntax.md

docs/usage_as_a_template_language.md: readme_src/README.yaml readme_src/template_language_usage.mext
	python -m mext.scripts.render_mext readme_src/template_language_usage.mext -o docs/usage_as_a_template_language.md

documents: docs/syntax.md docs/usage_as_a_template_language.md README.md


default: test clean install

install:
	pip install .

clean:
	rm -rdf dist/ build/ mext_lang.egg-info/

test:
	python -m unittest tests.test

readme_src/README.yaml: readme_src/README-yaml.yaml readme_src/README-yaml.mext
	python -m mext.scripts.render_mext readme_src/README-yaml.mext -o readme_src/README.yaml

README.md: readme_src/* docs/syntax.md docs/usage_as_a_template_language.md
	python -m mext.scripts.render_mext readme_src/README.mext -o README.md

docs/syntax.md: readme_src/README.yaml readme_src/syntax.mext tests/mext/readme/syntax/*
	python -m mext.scripts.render_mext readme_src/syntax.mext -o docs/syntax.md

docs/usage_as_a_template_language.md: readme_src/README.yaml readme_src/template_language_usage.mext  tests/mext/readme/template_language_usage/*
	python -m mext.scripts.render_mext readme_src/template_language_usage.mext -o docs/usage_as_a_template_language.md

documents: docs/syntax.md docs/usage_as_a_template_language.md README.md

.PHONY: build
build:
	pip install build
	rm -rf dist/*
	python -mbuild

.PHONY: test
test:
	PYTHONPATH=src python3 -munittest $(shell cd src ; grep -r -l '>>>' . | grep -v -e __pycache__ -e '\.py$$' )
	python3 -munittest tests/test*.py

run:
	PYTHONPATH=src python3 -m wordpress_markdown_blog_loader posts new \
		--title "Test Blog" \
		--author "Your Name" \
		--brand xebia.com  \
		--image $(PWD)/tests/resources/pexels-negativespace-34600.jpg \
 		--image-credits "Photo by [Negative Space](https://www.pexels.com/photo/coffee-writing-computer-blogging-34600/)" \
		--capability cloud

.PHONY: release
release: test build
	twine upload dist/*

.PHONY: release
clean:
	find . -type d -name __pycache__ | xargs rm -rf
	find . -type d -name \*.egg-info | xargs rm -rf
	find . -type f -name \*.pyc | xargs rm -rf
	rm -rf build dist .eggs

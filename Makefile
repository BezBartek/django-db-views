# Makefile
build:
	python -m build

check:
	twine check dist/*

deploy:
	twine upload dist/*

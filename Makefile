# Makefile
build:
	python setup.py sdist bdist_wheel

check:
	twine check dist/*

deploy:
	twine upload dist/*

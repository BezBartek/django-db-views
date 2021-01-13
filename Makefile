# Makefile
build:
	python setup.py sdist bdist_wheel
	twine check dist/*

deploy:
	twine upload dist/*

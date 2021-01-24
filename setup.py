import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="django-db-views",
    version="0.1.1",
    description="Handle database views. "
                "Allow to create migrations for database views. "
                "View migrations using django code. "
                "They can be reversed. "
                "Changes in model view definition are detected automatically. "
                "Support almost all options as regular makemigrations command",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/BezBartek/django-db-views",
    author="Bartłomiej Nowak and Mariusz Okulanis",
    author_email="n.bartek3762@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_packages(exclude=["test"]),
    include_package_data=True,
    install_requires=["Django", "six"],
    entry_points={},
)

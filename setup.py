import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="django-db-views",
    version="0.0.1",
    description="Allow to create view migrations for view models. "
                "Migrations uses django engine. "
                "They can be reversed, (they remember previous view definition). "
                "View definition changes inside view models are detected automatically."
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
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=["Django", "six"],
    entry_points={},
)

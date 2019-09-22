import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="example-pkg-your-username",
    version="1.0",
    author="syntaxaire",
    author_email="syntaxaire@gmail.com",
    description="Data extractors for the Caves of Qud roguelike",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/syntaxaire/hagadias",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
    ],
    python_requires='>=3.7',
)

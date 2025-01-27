import setuptools

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hfr_api",
    version="0.1.1",
    author="Vincent Roukine",
    author_email="vincent.roukine@gmail.com",
    description="A Python library to interface with forum.hardware.fr",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://gitea.ruk.info/roukine/hfr",
    packages=setuptools.find_packages(exclude=("tests", "tests.*")),
    install_requires=[],
    python_requires=">=3.13",
    include_package_data=True,
)

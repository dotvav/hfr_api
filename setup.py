import setuptools

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hfr_api",
    version="0.0.2",
    author="MycRub",
    author_email="mycrub@mycrub.net",
    description="A Python library to interface with forum.hardware.fr",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://gitea.ruk.info/roukine/hfr",
    packages=setuptools.find_packages(exclude=("tests", "tests.*")),
    install_requires=["requests","beautifulsoup4","sortedcontainers"],
    python_requires=">=3.13",
    include_package_data=True,
)

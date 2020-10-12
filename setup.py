import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="VSMD",
    version="0.1.9",
    author="jiangxt",
    author_email="624099049@qq.com",
    description="Controller for VSMD CAN motor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JChrysanthemum/VSMD",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=['python-can'],
)
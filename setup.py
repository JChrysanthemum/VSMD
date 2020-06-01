import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="VSMD", # Replace with your own username
    version="0.0.9",
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
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
import setuptools

__author__ = 'Sobolev Andrey <email.asobolev@gmail.com>'
__version__ = '0.0.1'

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='throw-catch',
    version=__version__,
    install_requires=['pika==1.3.1', 'orjson==3.8.3'],
    author='Sobolev Andrey',
    author_email='email.asobolev@gmail.com',
    description='RabbitMQ throw & catch messages',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    url="https://github.com/Sobolev5/throw-catch/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='yalesmartalarmclient',
    py_modules=['yalesmartalarmclient'],
    version='0.1.7',
    description='Interact with Yale Smart Alarm systems',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Dominic Willson',
    email='domwillcode@gmail.com',
    url='https://github.com/domwillcode/yale-smart-alarm-client',
    download_url='https://github.com/domwillcode/yale-smart-alarm-client',
    keywords=['alarm', 'Yale', 'Smart Alarm'],
    package_data={'': ['data/*.json']},
    install_requires=['requests>=2.0.0'],
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    license="Apache 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)

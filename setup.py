from setuptools import setup, find_packages

setup(
    name="signature-capture",
    version="0.1.0",
    description="Una librería para capturar y procesar firmas desde un Microcontrolador",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="JhordyR",
    author_email="jhordygg17@gmail.com",
    url="https://github.com/JhordyR/signature-capture",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyserial>=3.5",
        "Pillow>=9.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
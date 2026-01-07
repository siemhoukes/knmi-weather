from setuptools import setup

setup(
    name="knmi_weather",
    version="0.1.0",
    py_modules=["knmi_weather"],
    install_requires=["pandas", "requests"],
    author="Siem Houkes",
    description="Simple KNMI weather data fetcher",
    url="https://github.com/siemhoukes/knmi-weather",
    python_requires=">=3.9",
)

from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in zav_line_integration/__init__.py
from zav_line_integration import __version__ as version

setup(
	name="zav_line_integration",
	version=version,
	description="Get Line Shop Orders",
	author="Zaviago",
	author_email="muzammal.rasool1079@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

"""
WordPress Markdown blog loader
"""
from os import path
from setuptools import find_packages, setup

dependencies = [
    "requests",
    "markdown",
    "python-frontmatter",
    "click",
    "pytz",
    "Pillow",
    "binx-og-image-generator>=0.3.1",
    "markdownify",
    "bs4",
    "html5lib",
    "lxml",
    "python-slugify",
]

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="wordpress-markdown-blog-loader",
    version="0.5.3",
    url="https://github.com/binxio/wordpress-markdown-blog-loader",
    license="APL2",
    author="Mark van Holsteijn",
    author_email="markvanholsteijn@binx.io",
    description="load markdown blogs into wordpress",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    install_requires=dependencies,
    setup_requires=[],
    tests_require=dependencies + [],
    test_suite="tests",
    entry_points={
        "console_scripts": ["wp-md = wordpress_markdown_blog_loader.__main__:main"],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        "Development Status :: 4 - Beta",
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Operating System :: Unix",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

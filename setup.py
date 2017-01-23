"""
flask_admin_impexp
------------------

Description goes here...

Links
`````

* `documentation <http://packages.python.org/flask_admin_impexp>`_
* `development version
  <http://github.com/USERNAME/REPOSITORY/zipball/master#egg=flask_admin_impexp-dev>`_

"""
from setuptools import setup


setup(
    name='flask_admin_impexp',
    version='0.1',
    url='<enter URL here>',
    license='MIT',
    author='Saurabh Gupta',
    author_email='your-email-here@example.com',
    description='<enter short description here>',
    long_description=__doc__,
    package_data={'templates': ['*.html']},
    include_package_data=True,
    packages=['flask_admin_impexp'],
    namespace_packages=['flask_admin_impexp'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'flask-admin',
        'flask-excel',
        'tablib',
        'sqlalchemy'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

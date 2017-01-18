from setuptools import setup, find_packages

setup(
    name='pubnub',
    version='4.0.6',
    description='PubNub Real-time push service in the cloud',
    author='PubNub',
    author_email='support@pubnub.com',
    url='http://pubnub.com',
    packages=find_packages(exclude=("examples*", 'tests*')),
    license='MIT',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
    install_requires=[
        'pycrypto',
        'requests>=2.4',
        'requests-toolbelt',
        'six>=1.10'
    ],
    zip_safe=False,
)

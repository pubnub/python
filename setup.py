from setuptools import setup, find_packages

setup(
    name='pubnub',
    version='6.1.0',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
    install_requires=[
        'pycryptodomex>=3.3',
        'requests>=2.4',
        'cbor2',
        'aiohttp'
    ],
    zip_safe=False,
)

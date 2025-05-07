from setuptools import setup, find_packages

setup(
    name='pubnub',
    version='10.4.0',
    description='PubNub Real-time push service in the cloud',
    author='PubNub',
    author_email='support@pubnub.com',
    url='http://pubnub.com',
    project_urls={
        'Source': 'https://github.com/pubnub/python',
        'Documentation': 'https://www.pubnub.com/docs/sdks/python',
    },
    packages=find_packages(exclude=("examples*", 'tests*')),
    license='PubNub Software Development Kit License',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
    python_requires='>=3.7',
    install_requires=[
        'pycryptodomex>=3.3',
        'httpx>=0.28',
        'h2>=4.1',
        'requests>=2.32',
        'aiohttp>3.9.2',
        'cbor2>=5.6'
    ],
    zip_safe=False,
)

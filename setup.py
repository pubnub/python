from setuptools import setup, find_packages

setup(
    name='pubnub',
    version='3.7.1',
    description='PubNub Real-time push service in the cloud',
    author='Stephen Blum',
    author_email='support@pubnub.com',
    url='http://pubnub.com',
    py_modules=['Pubnub'],
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
        'pycrypto>=2.6.1',
        'requests>=2.4.0'
    ],
    zip_safe=False,
)

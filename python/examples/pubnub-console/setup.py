from setuptools import setup, find_packages

setup(
    name='pubnub-console',
    version='3.5.0-beta',
    description='PubNub Developer Console',
    author='Stephen Blum',
    author_email='support@pubnub.com',
    url='https://github.com/pubnub/python/raw/async/python/examples/pubnub-console/dist/pubnub-console-3.5.0-beta.tar.gz',
    scripts=['pubnub-console'],
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
        'pubnub==3.5.0-beta',
        'cmd2>=0.6.7',
    ],
    zip_safe=False,
)

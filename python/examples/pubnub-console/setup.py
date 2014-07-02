from setuptools import setup, find_packages

setup(
    name='pubnub-console',
    version='3.5.2',
    description='PubNub Developer Console',
    author='Stephen Blum',
    author_email='support@pubnub.com',
    url='http://pubnub.com',
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
        'pubnub>=3.5.2',
        'cmd2>=0.6.7',
        'pygments >= 1.6'
    ],
    zip_safe=False,
)

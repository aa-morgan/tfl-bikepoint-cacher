from setuptools import setup

setup(name='TfL-BikePoint-Cacher',
        version='0.0.1.dev',
        description='A tool for caching the TfL Cycle BikePoint data.',
        url='',
        author='Alex Morgan',
        author_email='axm108@gmail.com',
        license='GPL-3.0',
        packages=['bikepointcacher'],
        install_requires=[
            'tqdm'
        ],
        include_package_data=True,
        zip_safe=False)

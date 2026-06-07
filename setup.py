from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'OD'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
    ],
    install_requires=[
        'setuptools',   
        'ultralytics',
        'opencv-python',
    ],
    zip_safe=True,
    maintainer='sami',
    maintainer_email='sami@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'yolo_node=OD.yolo_node:main',

        ],
    },
)

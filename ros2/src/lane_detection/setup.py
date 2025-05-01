from setuptools import setup
import glob

package_name = 'lane_detection'

setup(
    name=package_name,
    version='0.0.1',
    packages=[],
    py_modules=[
        'lane_detection_node',
        'waypoint_transform_node',    
        'model',
        'postprocess_modify',
    ],
    package_dir={'': 'src'},

    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/models', glob.glob('models/**/*', recursive=True)),
        ('share/' + package_name + '/waypoints', glob.glob('waypoints/**/*', recursive=True)),
        ('share/' + package_name + '/waypoint_data', glob.glob('waypoint_data/**/*', recursive=True)),
        ('share/' + package_name + '/launch', glob.glob('launch/**/*', recursive=True)),
    ],

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your@email.com',
    description='SCNN lane detection and waypoint start point matching',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'lane_detection_node = lane_detection_node:main',
            'waypoint_transform_node = waypoint_transform_node:main',
            'start_point_match_node = start_point_match_node:main',  # ✅ 등록된 entry point
        ],
    },
)

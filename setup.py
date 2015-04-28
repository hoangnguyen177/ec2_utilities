from setuptools import setup

setup(name='ec2utils',
      version='0.1',
      description='ec2 utils',
      author='Hoang Nguyen',
      author_email='hoangnguyen177@gmail.com',
      url='https://github.com/hoangnguyen177/ec2_utilities.git',
      packages=['ec2utils'],
      zip_safe=False,
      data_files=[
          ('/usr/local/bin', ['ec2utils/ec2utils'])
      ],
      install_requires=[
        "boto>=2.34.0",
        "tabulate>=0.7.4"
        ]
)

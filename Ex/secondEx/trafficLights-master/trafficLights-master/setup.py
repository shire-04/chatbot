from setuptools import setup, find_packages

setup(name='hawksoft.trafficLights',
      version='1.0.0',
      packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # 多文件模块写法
      author="xingyongkang",
      author_email="xingyongkang@cqu.edu.cn",
      description="Knowledge base using pyknow for controlling traffic lights",
      long_description=open('./README.md', encoding='utf-8').read(),
      long_description_content_type = "text/markdown",
      #long_description="http://gitee.comg/xingyongkang",
      license="MIT",
      url = "https://gitee.com/xingyongkang/trafficLights",
      include_package_data=True,
      platforms="any",
      install_requires=['pyserial','pyknow'],
      keywords='pyknow, traffic lights, production system',
      entry_points={
          'console_scripts': [
              'trafficLights = hawksoft.trafficLights:main'
          ]
      }
)
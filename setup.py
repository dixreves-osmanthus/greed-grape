from setuptools import setup, find_packages

setup(
    name='StudyHub',
    version='1.0.0',
    description='A comprehensive education resource platform for high school and university students',
    author='StudyHub Team',
    author_email='info@studyhub.com',
    packages=find_packages(),
    install_requires=[
        'Flask==3.0.0',
        'Flask-SQLAlchemy==3.1.1',
        'Flask-Login==0.6.3',
        'Flask-WTF==1.1.1',
        'WTForms==3.1.2',
        'reportlab==4.1.0',
        'PyPDF2==3.0.1',
        'python-dotenv==1.0.0',
        'bcrypt==4.1.1',
        'email-validator==2.1.0',
        'Pillow==10.1.0',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'studyhub=run:app',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)

# StudyHub - Education Resource Platform

A comprehensive web application for high school and university students to access, share, and manage educational resources including questions, essays, handouts, and exam papers.

## Features

### 1. Dynamic Question Paper Generation
- **Question Bank**: Extensive collection of questions across various subjects and difficulty levels
- **Custom Paper Generation**: Create question papers by selecting:
  - Number of questions
  - Specific categories
  - Difficulty levels (Easy, Medium, Hard)
  - Include/exclude answer key
- **PDF Download**: Generated papers can be downloaded as PDF
- **Online Preview**: View questions directly on the page

### 2. Static Content Management
- **Essays**: Collection of academic essays across various topics
- **Handouts**: Lecture notes, study guides, and handouts
- **PDF Generation**: Convert documents to PDF format
- **Downloadable Content**: All documents available for download as PDF

### 3. Upload Portal
- **Question Papers**: Upload past exam papers for others to access
- **Essays and Handouts**: Share your own documents with the community
- **Question Bank Contributions**: Add questions to the shared bank
- **Approval System**: All uploads are reviewed by administrators

### 4. Administrative Panel
- **User Management**: Create, edit, and delete user accounts
- **Content Moderation**: Approve or reject uploaded content
- **Category Management**: Organize questions and documents by categories
- **Statistics Dashboard**: View platform usage statistics
- **Bulk Operations**: Approve/reject multiple items at once

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (default), can be configured for MySQL/PostgreSQL
- **Authentication**: Flask-Login for user sessions
- **PDF Generation**: ReportLab for dynamic PDF creation
- **Frontend**: Bootstrap 5, Font Awesome icons
- **File Handling**: Secure file upload and management

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git (optional, for cloning)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dixreves-osmanthus/greed-grape.git
   cd greed-grape
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application:**
   - Copy `.env.example` to `.env` and update the settings:
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` to set your SECRET_KEY and other configurations

5. **Initialize the database:**
   ```bash
   flask shell
   >>> from app import db, create_app
   >>> app = create_app()
   >>> with app.app_context():
   ...     db.create_all()
   ...     exit()
   ```

6. **Run the application:**
   ```bash
   python run.py
   ```

7. **Access the application:**
   - Open your browser and go to: `http://localhost:5000`
   - Admin login: `admin@example.com` / `admin123`

### Production Deployment

For production deployment, consider:

1. **Use a production WSGI server:**
   - Gunicorn: `pip install gunicorn`
   - Run with: `gunicorn -w 4 -b 0.0.0.0:8000 run:app`

2. **Use a proper database:**
   - MySQL: `SQLALCHEMY_DATABASE_URI=mysql://user:password@localhost/dbname`
   - PostgreSQL: `SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost/dbname`

3. **Set up environment variables:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secret-key
   export SQLALCHEMY_DATABASE_URI=your-database-uri
   ```

4. **Use a reverse proxy:**
   - Nginx or Apache for static file serving and SSL termination

## Project Structure

```
greed-grape/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── models.py            # Database models
│   ├── config.py            # Configuration settings
│   ├── routes.py            # Main application routes
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── pdf_generator.py # PDF generation utilities
│   │   ├── file_handler.py  # File upload/management
│   │   └── helpers.py       # Helper functions
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py        # Authentication routes
│   │   └── forms.py         # Authentication forms
│   ├── upload/
│   │   ├── __init__.py
│   │   ├── routes.py        # Upload routes
│   │   └── forms.py         # Upload forms
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── routes.py        # Admin routes
│   │   └── forms.py         # Admin forms
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints
│   ├── static/
│   │   ├── css/             # CSS files
│   │   ├── js/              # JavaScript files
│   │   └── uploads/         # Uploaded files
│   └── templates/           # HTML templates
│       ├── base.html        # Base template
│       ├── index.html       # Home page
│       ├── auth/            # Authentication templates
│       ├── questions/       # Question-related templates
│       ├── documents/       # Document templates
│       ├── papers/          # Exam paper templates
│       ├── upload/          # Upload templates
│       └── admin/           # Admin templates
├── config.py                # Configuration
├── run.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Usage

### For Students

1. **Browse Resources:**
   - Navigate to High School or University section
   - Browse questions, documents, or exam papers by category
   - Use filters to find specific content

2. **Generate Question Papers:**
   - Go to "Generate Question Paper" section
   - Select your preferences (categories, difficulty, number of questions)
   - Click "Generate" to create a custom paper
   - Download as PDF or view online

3. **Download Content:**
   - Click "Download" on any document or exam paper
   - Content is available in PDF format

### For Contributors

1. **Register an Account:**
   - Click "Register" on the home page
   - Fill in your details and create an account

2. **Upload Content:**
   - Go to the Upload Center for your level
   - Choose what to upload (questions, documents, or exam papers)
   - Fill in the required information
   - Upload your file

3. **Manage Uploads:**
   - View all your uploads in "My Uploads"
   - Track approval status
   - Delete your own uploads

### For Administrators

1. **Login:**
   - Use admin credentials (default: admin@example.com / admin123)

2. **Dashboard:**
   - View platform statistics
   - See recent activity
   - Access quick actions

3. **Manage Content:**
   - Approve or reject pending uploads
   - Edit or delete any content
   - Organize categories

4. **User Management:**
   - Create new user accounts
   - Edit user information
   - Delete users

## API Endpoints

The application provides RESTful API endpoints for integration:

### Questions
- `GET /api/questions/<level>` - Get questions for a level
- `GET /api/questions/random/<level>` - Get random questions
- `POST /api/questions/generate-pdf/<level>` - Generate PDF question paper

### Documents
- `GET /api/documents/<level>` - Get documents for a level
- `GET /api/categories/documents/<level>` - Get document categories

### Exam Papers
- `GET /api/papers/<level>` - Get exam papers for a level

### Categories
- `GET /api/categories/questions/<level>` - Get question categories

## Security Features

- **User Authentication**: Secure login system with password hashing
- **CSRF Protection**: Built-in Flask-WTF CSRF protection
- **File Upload Security**: 
  - File type validation
  - Maximum file size limits
  - Secure file naming
- **Authorization**: Role-based access control (admin vs regular users)
- **Approval System**: All user uploads require admin approval

## Customization

### Changing File Upload Settings

Edit `config.py`:
```python
MAX_CONTENT_LENGTH = 16777216  # 16MB
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
```

### Adding New Content Types

1. Add new model in `app/models.py`
2. Create corresponding routes in `app/routes.py` or new blueprint
3. Add templates for the new content type
4. Update navigation menu in `base.html`

### Changing Styling

Edit `app/static/css/style.css` for custom styles or override Bootstrap classes.

## Troubleshooting

### Database Issues
- If you get database errors, try deleting the database file and recreating it
- Ensure you have write permissions in the project directory

### File Upload Issues
- Check that the upload folder exists and has write permissions
- Verify file types are in the allowed extensions list
- Ensure files are not exceeding the maximum size limit

### Login Issues
- Verify the user exists in the database
- Check that the password is correct
- Ensure you're using the correct email address

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions or issues, please open a GitHub issue or contact the maintainer.

---

**Built with Flask and Love for Education**

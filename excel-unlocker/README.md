# Excel Unlocker

A web application to remove password protection from Excel files.

## Features

- Remove password protection from Excel files (.xlsx, .xlsm, .xltx, .xltm)
- Simple and intuitive web interface
- Secure file handling with automatic cleanup
- Works with password-protected Excel files

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/DocTools.git
   cd DocTools/excel-unlocker
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server:
   ```bash
   python app.py
   ```

5. Open http://localhost:5000 in your browser

## Deployment

### Apache with mod_wsgi

1. Install required packages:
   ```bash
   sudo apt-get install apache2 libapache2-mod-wsgi-py3
   ```

2. Configure Apache:
   ```apache
   <VirtualHost *:80>
       ServerName yourdomain.com
       
       WSGIDaemonProcess excel_unlocker python-path=/path/to/DocTools/excel-unlocker
       WSGIProcessGroup excel_unlocker
       WSGIScriptAlias / /path/to/DocTools/excel-unlocker/wsgi.py
       
       <Directory /path/to/DocTools/excel-unlocker>
           Options -Indexes -FollowSymLinks
           AllowOverride All
           Require all granted
       </Directory>
   </VirtualHost>
   ```

3. Set proper permissions:
   ```bash
   sudo chown -R www-data:www-data /path/to/DocTools/excel-unlocker
   sudo chmod -R 755 /path/to/DocTools/excel-unlocker
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=106 * 1024 * 1024  # 106MB
```

## Security

- All uploaded files are automatically deleted after processing
- Directory listing is disabled
- Sensitive files are protected from direct access
- Secure headers are set for all responses

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

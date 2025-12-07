# Dalil Docs - Islamic Reference Library

## Overview

Dalil Docs is a Flask-based web application serving as an Islamic reference library platform. The application provides access to PDFs of Islamic texts, organized references (hawala jaat) by topic, and a Q&A system where users can ask questions and receive answers from administrators. The interface is primarily in Urdu (using RTL layout) with Material Design-inspired styling.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Template System**: Server-side rendering using Jinja2 templates with a base template pattern
- `base.html` provides the common layout structure with RTL (right-to-left) Urdu support
- All pages extend the base template for consistent navigation and styling
- Custom CSS embedded in base template using CSS variables for theming

**Design System**:
- Material Design principles with minimalist execution
- Color scheme: Green primary (#2d5f3f), gold accent (#d4af37), light backgrounds
- Typography: Urdu fonts (Noto Nastaliq Urdu, Jameel Noori Nastaleeq) with fallbacks
- Responsive grid layout using flexbox
- Card-based component architecture for content organization

**UI Components**:
- Sticky header with gradient background
- Card containers for content blocks
- Button system with primary, accent, and danger variants
- Form inputs with consistent styling
- Grid layouts for dashboard and content listings

### Backend Architecture

**Web Framework**: Flask with SQLAlchemy ORM for database operations

**Route Structure**:
- Public routes: Home, PDFs listing/viewing, references by topic, Q&A submission
- Admin routes: Dashboard, PDF management, reference management, question management, admin user management
- Authentication: Session-based with device ID tracking for admins

**Authentication & Authorization**:
- Session-based authentication using Flask sessions
- Hard-coded main admin password for initial access
- Device ID verification for multi-device admin access
- Main admin vs regular admin role distinction
- Password verification required for sensitive operations (admin management)

**File Upload System**:
- PDF file uploads stored in `uploads/pdfs/` directory
- 50MB file size limit
- Secure filename handling using Werkzeug utilities
- File serving for both viewing and downloading

### Data Storage

**Database**: SQLite (`dalildocs.db`) with SQLAlchemy ORM

**Schema Design**:

1. **Admin Model**: Stores administrator accounts
   - Fields: id, username, password, device_id, is_main
   - Supports multiple admin users with role differentiation

2. **PDF Model**: Manages uploaded Islamic texts
   - Fields: id, title, filename, uploaded_at
   - Simple structure for document management

3. **Topic Model**: Organizes reference categories
   - Fields: id, name
   - One-to-many relationship with references

4. **Reference Model**: Stores detailed Islamic references
   - Fields: id, topic_id, title, content
   - Foreign key relationship to Topic
   - Text field for detailed content storage

5. **Question Model**: Q&A system data
   - Fields: id, user_name, question, reply_message, reply_reference
   - Supports both message and reference-based replies
   - Status tracking (pending/answered) implied by presence of reply data

**Relationship Patterns**:
- Topic → References (one-to-many via SQLAlchemy backref)
- No explicit user authentication for question askers (name-based identification)

### Key Architectural Decisions

**Session Management**:
- 30-day persistent sessions for admin convenience
- Device ID tracking allows admins to use multiple devices
- Secret key for session encryption

**File Organization**:
- PDFs stored in filesystem rather than database for performance
- Upload folder structure: `uploads/pdfs/`
- Files served directly via Flask routes with send_file

**Bilingual Interface**:
- Primary language: Urdu (RTL layout)
- UI labels and text in Roman Urdu for accessibility
- Date formatting localized to DD-MM-YYYY format

**User Experience Patterns**:
- Name-based question tracking (localStorage persistence)
- Users can view their questions by entering their name
- No formal user registration required for public features
- Admin features behind authentication wall

**Question Workflow**:
- Users submit questions with name and question text
- Admins see pending questions in dashboard
- Admins can reply with message and/or reference citation
- Users can check status by searching their name

## External Dependencies

### Python Packages
- **Flask**: Web framework for routing and request handling
- **Flask-SQLAlchemy**: ORM for database operations
- **Werkzeug**: Utilities for secure filename handling and file operations

### Frontend Resources
- **Google Fonts CDN**: Urdu fonts (Noto Nastaliq Urdu, Jameel Noori Nastaleeq)
- No JavaScript frameworks - vanilla JavaScript for minimal interactivity

### Database
- **SQLite**: Embedded database (file: `dalildocs.db`)
- No external database server required

### Third-Party Integrations
- **Instagram**: Social media links embedded in homepage (display only, no API integration)
- No external APIs or services integrated
- No email service configured for notifications

### File System Dependencies
- Local file storage for PDF uploads
- Directories created programmatically: `uploads/pdfs/`


# Breathe ESG Tech Intern Assignment

## Overview

This project is a prototype ESG data ingestion and review platform built using Django REST Framework and React. The application ingests enterprise sustainability data from different sources, normalizes it into a common format, and provides an analyst review workflow before records are locked for auditing.

Supported data sources:

- SAP fuel and procurement data
- Utility electricity data
- Corporate travel data


## Features

- Multi-source data ingestion
- Data normalization
- Source tracking
- Scope 1, Scope 2, Scope 3 categorization
- Multi-tenant support
- Analyst review dashboard
- Approval workflow
- Audit trail
- Suspicious record detection

## Technology Stack

### Backend
- Django
- Django REST Framework
- PostgreSQL
- JWT Authentication

### Frontend
- React
- Vite
- Tailwind CSS
- Axios

### Deployment
- Frontend: Vercel
- Backend: Render


## Source Handling

### SAP Fuel and Procurement Data

Input Method:
- CSV Upload

Handled Fields:
- Plant Code
- Material
- Quantity
- Unit
- Date
- Cost Center

Challenges Handled:
- Unit inconsistencies
- Date normalization
- Source mapping


### Utility Electricity Data

Input Method:
- CSV Upload

Handled Fields:
- Meter ID
- Billing Period Start
- Billing Period End
- Electricity Consumption

Challenges Handled:
- Non-calendar billing periods
- Unit normalization


### Corporate Travel Data

Input Method:
- CSV Upload

Handled Fields:
- Employee Name
- Origin Airport
- Destination Airport
- Travel Category
- Distance

Challenges Handled:
- Missing distances
- Travel category mapping


## Application Workflow

1. Upload source files
2. Store raw records
3. Normalize data
4. Identify suspicious records
5. Review through dashboard
6. Approve records
7. Lock records for audit


## Project Structure
BreatheESG/
│
├── backend/
├── frontend/
├── MODEL.md
├── DECISIONS.md
├── TRADEOFFS.md
├── SOURCES.md
├── README.md



---

## Deployment

Frontend URL
https://breatheesg-sandy.vercel.app/

Backend URL:

https://breathe-esg-backend-lxcp.onrender.com

GitRepository:

https://github.com/Guntamadugupavankumar/Breathe-ESG

**backend configuration and setup**
link: http://127.0.0.1:8000/
cd backend,
python manage.py makemigrations,
python manage.py migrate,
python manage.py createsuperuser,
python manage.py runserver,

**frontend configuration and setup**
link: http://localhost:5173/
cd frontend,
npm install,
npm run dev,

## Demo Credentials

Username: pandu123

Password: pandu123

## Author

 Guntamadugu Pavan Kumar

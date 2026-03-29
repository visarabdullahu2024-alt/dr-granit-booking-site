# Dr. Granit Abdullahu Booking App

Simple booking web app for a thoracic surgeon with:

- doctor profile and services
- multiple clinic locations
- public booking form with appointment reason
- doctor dashboard login
- ability to lock days or hours
- in-app notifications for new bookings
- optional email alerts when SMTP is configured

## Run locally

```bash
cd "/Users/vis/Documents/New project/app"
python3 server.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Doctor dashboard login

- Email: `doctor@granitabdullahu.local`
- Password: `Doctor123!`

Doctor dashboard page:

- `http://127.0.0.1:8000/doctor.html`

You can change the password with:

```bash
export DOCTOR_DASHBOARD_PASSWORD="your-new-password"
python3 server.py
```

## Environment variables

- `DOCTOR_APP_HOST` default `127.0.0.1`
- `DOCTOR_APP_PORT` default `8000`
- `DOCTOR_APP_DB_PATH` default `./doctor_booking.db`
- `DOCTOR_APP_CORS_ORIGIN` default `*`
- `DOCTOR_DASHBOARD_PASSWORD` default `Doctor123!`
- `DOCTOR_PUBLIC_EMAIL` public email shown on the website
- `DOCTOR_NOTIFICATION_EMAIL` email that receives new booking alerts
- `DOCTOR_NOTIFICATION_PHONE` doctor phone label shown in UI
- `SMTP_HOST` SMTP server hostname for booking emails
- `SMTP_PORT` default `587`
- `SMTP_USERNAME` SMTP username
- `SMTP_PASSWORD` SMTP password
- `SMTP_FROM_EMAIL` sender email override

## Free deployment

This project includes [`render.yaml`](/Users/vis/Documents/New project/render.yaml) for free deployment on Render.

### Render steps

1. Push the project to GitHub.
2. In Render, choose `New +` then `Blueprint`.
3. Connect the repo and deploy.
4. Open the generated URL after build completes.

### Important free-tier note

The current free setup stores SQLite in `/tmp/doctor_booking.db`, so data can reset after restarts or redeploys.

For durable production use, the next step should be moving bookings and locks to PostgreSQL or Supabase.

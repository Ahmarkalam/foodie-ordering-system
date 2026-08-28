# Foodie V4 — Zomato-inspired Food Ordering System

## Local setup
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Admin
Email: admin@foodie.com
Password: Admin@123

## Included
Customer login/register, sidebar dashboard navigation, profile, addresses, favorites, restaurant discovery, search, menus, functional cart, quantity controls, coupons, checkout, COD, order history, tracking, reorder, cancellation, reviews, admin order status, restaurant and dish management, analytics, PostgreSQL/Render deployment files.

## Payment
COD is fully functional. The online-payment option is deliberately not a fake success flow. Add real Razorpay server-side order creation/signature verification and credentials before accepting live online payments.

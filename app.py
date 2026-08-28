from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os, secrets

app=Flask(__name__)
app.config["SECRET_KEY"]=os.environ.get("SECRET_KEY",secrets.token_hex(32))
app.config["SQLALCHEMY_DATABASE_URI"]=os.environ.get("DATABASE_URL","sqlite:///foodie.db").replace("postgres://","postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(150),unique=True,nullable=False); password=db.Column(db.String(255),nullable=False)
    role=db.Column(db.String(20),default="customer"); phone=db.Column(db.String(30),default="")
    addresses=db.relationship("Address",backref="user",cascade="all, delete-orphan")
class Address(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    label=db.Column(db.String(30),default="Home"); address=db.Column(db.String(400),nullable=False)
    phone=db.Column(db.String(30),default=""); is_default=db.Column(db.Boolean,default=False)
class Restaurant(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(140),nullable=False)
    cuisine=db.Column(db.String(150),nullable=False); description=db.Column(db.String(500),default="")
    address=db.Column(db.String(300),default=""); rating=db.Column(db.Float,default=4.5)
    delivery_time=db.Column(db.String(40),default="25-35 min"); delivery_fee=db.Column(db.Float,default=40)
    min_order=db.Column(db.Float,default=199); image=db.Column(db.String(700),default=""); is_open=db.Column(db.Boolean,default=True)
    items=db.relationship("FoodItem",backref="restaurant",cascade="all, delete-orphan")
class FoodItem(db.Model):
    id=db.Column(db.Integer,primary_key=True); restaurant_id=db.Column(db.Integer,db.ForeignKey("restaurant.id"),nullable=False)
    name=db.Column(db.String(140),nullable=False); description=db.Column(db.String(400),default="")
    price=db.Column(db.Float,nullable=False); category=db.Column(db.String(60),nullable=False)
    image=db.Column(db.String(700),default=""); popular=db.Column(db.Boolean,default=False); available=db.Column(db.Boolean,default=True)
class Favorite(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    food_id=db.Column(db.Integer,nullable=False)
    __table_args__=(db.UniqueConstraint("user_id","food_id",name="uq_favorite"),)
class Offer(db.Model):
    id=db.Column(db.Integer,primary_key=True); restaurant_id=db.Column(db.Integer,db.ForeignKey("restaurant.id"),nullable=True)
    title=db.Column(db.String(160),nullable=False); code=db.Column(db.String(40),unique=True,nullable=False)
    discount_type=db.Column(db.String(20),default="flat"); value=db.Column(db.Float,default=0); min_order=db.Column(db.Float,default=0); active=db.Column(db.Boolean,default=True)
class Order(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    restaurant_id=db.Column(db.Integer,db.ForeignKey("restaurant.id"),nullable=False); customer_name=db.Column(db.String(100),nullable=False)
    phone=db.Column(db.String(30),nullable=False); address=db.Column(db.String(400),nullable=False)
    subtotal=db.Column(db.Float,nullable=False); delivery_fee=db.Column(db.Float,default=0); discount=db.Column(db.Float,default=0); total=db.Column(db.Float,nullable=False)
    coupon=db.Column(db.String(40),default=""); payment_method=db.Column(db.String(40),default="COD"); payment_status=db.Column(db.String(30),default="Pending")
    status=db.Column(db.String(40),default="Order Placed"); created_at=db.Column(db.DateTime,default=datetime.utcnow)
    items=db.relationship("OrderItem",backref="order",cascade="all, delete-orphan"); restaurant=db.relationship("Restaurant")
class OrderItem(db.Model):
    id=db.Column(db.Integer,primary_key=True); order_id=db.Column(db.Integer,db.ForeignKey("order.id"),nullable=False)
    food_id=db.Column(db.Integer,nullable=False); food_name=db.Column(db.String(140),nullable=False); price=db.Column(db.Float,nullable=False); quantity=db.Column(db.Integer,nullable=False)
class Review(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    restaurant_id=db.Column(db.Integer,db.ForeignKey("restaurant.id"),nullable=False); rating=db.Column(db.Integer,nullable=False)
    text=db.Column(db.String(500),default=""); created_at=db.Column(db.DateTime,default=datetime.utcnow); user=db.relationship("User")

def login_required(f):
    @wraps(f)
    def w(*a,**kw):
        if not session.get("user_id"): flash("Please login first.","error"); return redirect(url_for("login",next=request.path))
        return f(*a,**kw)
    return w
def admin_required(f):
    @wraps(f)
    def w(*a,**kw):
        if session.get("role")!="admin": flash("Admin access required.","error"); return redirect(url_for("login"))
        return f(*a,**kw)
    return w

@app.context_processor
def globals():
    cart=session.get("cart",{}); fav=set()
    if session.get("user_id"): fav={x.food_id for x in Favorite.query.filter_by(user_id=session["user_id"]).all()}
    return {"cart_count":sum(cart.values()),"favorite_ids":fav}

def cart_rows():
    rows=[]; subtotal=0
    for k,q in session.get("cart",{}).items():
        item=db.session.get(FoodItem,int(k))
        if item and item.available and item.restaurant.is_open:
            line=item.price*q; subtotal+=line; rows.append((item,q,line))
    return rows,subtotal

@app.route("/")
def index():
    return render_template("home.html",restaurants=Restaurant.query.filter_by(is_open=True).order_by(Restaurant.rating.desc()).all(),
                           popular=FoodItem.query.filter_by(available=True,popular=True).limit(8).all(),
                           offers=Offer.query.filter_by(active=True).all())
@app.route("/restaurants")
def restaurants():
    q=request.args.get("q","").strip(); query=Restaurant.query
    if q: query=query.filter(db.or_(Restaurant.name.ilike(f"%{q}%"),Restaurant.cuisine.ilike(f"%{q}%")))
    return render_template("restaurants.html",restaurants=query.order_by(Restaurant.rating.desc()).all(),q=q)
@app.route("/restaurant/<int:rid>")
def restaurant(rid):
    r=db.get_or_404(Restaurant,rid); items=FoodItem.query.filter_by(restaurant_id=rid,available=True).order_by(FoodItem.popular.desc()).all()
    reviews=Review.query.filter_by(restaurant_id=rid).order_by(Review.created_at.desc()).all()
    return render_template("restaurant.html",restaurant=r,items=items,reviews=reviews)
@app.route("/menu")
def menu():
    q=request.args.get("q","").strip(); c=request.args.get("category","All"); query=FoodItem.query.filter_by(available=True)
    if c!="All": query=query.filter_by(category=c)
    if q: query=query.filter(db.or_(FoodItem.name.ilike(f"%{q}%"),FoodItem.description.ilike(f"%{q}%")))
    cats=[x[0] for x in db.session.query(FoodItem.category).filter_by(available=True).distinct().all()]
    return render_template("menu.html",items=query.order_by(FoodItem.popular.desc()).all(),categories=cats,category=c,q=q)
@app.post("/cart/add/<int:fid>")
def add_to_cart(fid):
    item=db.get_or_404(FoodItem,fid); cart=session.get("cart",{})
    if not item.available or not item.restaurant.is_open: flash("Item unavailable.","error"); return redirect(request.referrer or url_for("menu"))
    if cart:
        first=db.session.get(FoodItem,int(next(iter(cart))))
        if first and first.restaurant_id!=item.restaurant_id: flash("Cart contains another restaurant. Clear it first.","error"); return redirect(request.referrer or url_for("menu"))
    cart[str(fid)]=min(cart.get(str(fid),0)+1,20); session["cart"]=cart; flash(f"{item.name} added to cart.","success"); return redirect(request.referrer or url_for("menu"))
@app.route("/cart")
def cart():
    rows,subtotal=cart_rows(); r=rows[0][0].restaurant if rows else None; delivery=r.delivery_fee if r and subtotal<499 else 0
    return render_template("cart.html",rows=rows,subtotal=subtotal,delivery=delivery,total=subtotal+delivery,restaurant=r)
@app.post("/cart/update")
def cart_update():
    cart=session.get("cart",{})
    for k,v in request.form.items():
        if k.startswith("qty_"):
            try:q=max(0,min(20,int(v)))
            except:q=1
            if q: cart[k[4:]]=q
            else: cart.pop(k[4:],None)
    session["cart"]=cart; return redirect(url_for("cart"))
@app.post("/cart/remove/<int:fid>")
def cart_remove(fid):
    c=session.get("cart",{}); c.pop(str(fid),None); session["cart"]=c; return redirect(url_for("cart"))
@app.post("/cart/clear")
def cart_clear(): session["cart"]={}; return redirect(url_for("cart"))

@app.route("/checkout",methods=["GET","POST"])
@login_required
def checkout():
    rows,subtotal=cart_rows()
    if not rows: return redirect(url_for("menu"))
    r=rows[0][0].restaurant; delivery=r.delivery_fee if subtotal<499 else 0; discount=0; coupon=""
    user=db.get_or_404(User,session["user_id"])
    if request.method=="POST":
        coupon=request.form.get("coupon","").strip().upper(); offer=Offer.query.filter_by(code=coupon,active=True).first() if coupon else None
        if offer and subtotal>=offer.min_order and (offer.restaurant_id is None or offer.restaurant_id==r.id):
            discount=round(subtotal*offer.value/100,2) if offer.discount_type=="percent" else min(offer.value,subtotal)
        elif coupon: flash("Coupon invalid or minimum order not met.","error")
        if request.form.get("place_order"):
            o=Order(user_id=user.id,restaurant_id=r.id,customer_name=request.form["customer_name"],phone=request.form["phone"],address=request.form["address"],
                    subtotal=subtotal,delivery_fee=delivery,discount=discount,total=max(0,subtotal+delivery-discount),coupon=coupon if discount else "",
                    payment_method=request.form.get("payment_method","COD"))
            db.session.add(o); db.session.flush()
            for item,q,line in rows: db.session.add(OrderItem(order_id=o.id,food_id=item.id,food_name=item.name,price=item.price,quantity=q))
            db.session.commit(); session["cart"]={}; return redirect(url_for("order",oid=o.id))
    return render_template("checkout.html",user=user,restaurant=r,subtotal=subtotal,delivery=delivery,discount=discount,total=subtotal+delivery-discount,
                           coupon=coupon,addresses=user.addresses)
@app.route("/orders")
@login_required
def orders(): return render_template("orders.html",orders=Order.query.filter_by(user_id=session["user_id"]).order_by(Order.created_at.desc()).all())
@app.route("/order/<int:oid>")
@login_required
def order(oid):
    o=db.get_or_404(Order,oid)
    if o.user_id!=session["user_id"] and session.get("role")!="admin": return redirect(url_for("orders"))
    return render_template("order.html",order=o)
@app.post("/order/<int:oid>/cancel")
@login_required
def cancel(oid):
    o=db.get_or_404(Order,oid)
    if o.user_id==session["user_id"] and o.status in ["Order Placed","Preparing"]: o.status="Cancelled"; db.session.commit()
    return redirect(url_for("order",oid=oid))
@app.post("/order/<int:oid>/reorder")
@login_required
def reorder(oid):
    o=db.get_or_404(Order,oid); session["cart"]={}
    for x in o.items:
        item=db.session.get(FoodItem,x.food_id)
        if item and item.available and item.restaurant.is_open: session["cart"][str(item.id)]=x.quantity
    return redirect(url_for("cart"))
@app.post("/favorite/<int:fid>")
@login_required
def favorite(fid):
    f=Favorite.query.filter_by(user_id=session["user_id"],food_id=fid).first()
    if f: db.session.delete(f); state=False
    else: db.session.add(Favorite(user_id=session["user_id"],food_id=fid)); state=True
    db.session.commit(); return jsonify(ok=True,favorite=state)
@app.route("/favorites")
@login_required
def favorites():
    ids=[x.food_id for x in Favorite.query.filter_by(user_id=session["user_id"]).all()]
    return render_template("favorites.html",items=FoodItem.query.filter(FoodItem.id.in_(ids)).all() if ids else [])
@app.route("/profile",methods=["GET","POST"])
@login_required
def profile():
    u=db.get_or_404(User,session["user_id"])
    if request.method=="POST":
        u.name=request.form["name"].strip(); u.phone=request.form.get("phone","").strip()
        if request.form.get("password"): u.password=generate_password_hash(request.form["password"])
        db.session.commit(); session["user_name"]=u.name; flash("Profile updated.","success")
    return render_template("profile.html",user=u,addresses=u.addresses)
@app.post("/address/add")
@login_required
def address_add():
    if request.form.get("is_default"): Address.query.filter_by(user_id=session["user_id"]).update({"is_default":False})
    db.session.add(Address(user_id=session["user_id"],label=request.form.get("label","Home"),address=request.form["address"],phone=request.form.get("phone",""),is_default=bool(request.form.get("is_default"))))
    db.session.commit(); return redirect(url_for("profile"))
@app.post("/address/delete/<int:aid>")
@login_required
def address_delete(aid):
    a=db.get_or_404(Address,aid)
    if a.user_id==session["user_id"]: db.session.delete(a); db.session.commit()
    return redirect(url_for("profile"))
@app.post("/review/<int:rid>")
@login_required
def review(rid):
    db.session.add(Review(user_id=session["user_id"],restaurant_id=rid,rating=max(1,min(5,int(request.form["rating"]))),text=request.form.get("text","")[:500]))
    r=db.get_or_404(Restaurant,rid); db.session.commit(); rs=Review.query.filter_by(restaurant_id=rid).all(); r.rating=round(sum(x.rating for x in rs)/len(rs),1); db.session.commit()
    return redirect(url_for("restaurant",rid=rid))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if not u or not check_password_hash(u.password,request.form["password"]): flash("Invalid login.","error"); return render_template("login.html")
        session.update(user_id=u.id,user_name=u.name,role=u.role); return redirect(request.args.get("next") or url_for("index"))
    return render_template("login.html")
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        if User.query.filter_by(email=email).first(): flash("Email already registered.","error"); return render_template("register.html")
        u=User(name=request.form["name"].strip(),email=email,password=generate_password_hash(request.form["password"]),phone=request.form.get("phone",""))
        db.session.add(u); db.session.commit(); session.update(user_id=u.id,user_name=u.name,role="customer"); return redirect(url_for("index"))
    return render_template("register.html")
@app.get("/logout")
def logout(): session.clear(); return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin():
    orders=Order.query.order_by(Order.created_at.desc()).all(); rs=Restaurant.query.all(); items=FoodItem.query.all()
    stats={"orders":len(orders),"revenue":sum(o.total for o in orders if o.status!="Cancelled"),"customers":User.query.filter_by(role="customer").count(),"restaurants":len(rs)}
    return render_template("admin.html",orders=orders,restaurants=rs,items=items,stats=stats)
@app.post("/admin/order/<int:oid>/status")
@admin_required
def admin_status(oid):
    o=db.get_or_404(Order,oid); o.status=request.form["status"]; db.session.commit(); return redirect(url_for("admin"))
@app.post("/admin/restaurant")
@admin_required
def admin_restaurant():
    db.session.add(Restaurant(name=request.form["name"],cuisine=request.form["cuisine"],description=request.form["description"],address=request.form["address"],
                              delivery_time=request.form["delivery_time"],delivery_fee=float(request.form["delivery_fee"]),min_order=float(request.form["min_order"]),image=request.form["image"]))
    db.session.commit(); return redirect(url_for("admin"))
@app.post("/admin/restaurant/<int:rid>/toggle")
@admin_required
def admin_rest_toggle(rid):
    r=db.get_or_404(Restaurant,rid); r.is_open=not r.is_open; db.session.commit(); return redirect(url_for("admin"))
@app.post("/admin/food")
@admin_required
def admin_food():
    db.session.add(FoodItem(restaurant_id=int(request.form["restaurant_id"]),name=request.form["name"],description=request.form["description"],price=float(request.form["price"]),
                            category=request.form["category"],image=request.form["image"],popular=bool(request.form.get("popular"))))
    db.session.commit(); return redirect(url_for("admin"))
@app.post("/admin/food/<int:fid>/toggle")
@admin_required
def admin_food_toggle(fid):
    i=db.get_or_404(FoodItem,fid); i.available=not i.available; db.session.commit(); return redirect(url_for("admin"))

def seed():
    db.create_all()
    if not User.query.filter_by(email="admin@foodie.com").first():
        db.session.add(User(name="Foodie Admin",email="admin@foodie.com",password=generate_password_hash("Admin@123"),role="admin"))
    if Restaurant.query.count()==0:
        data=[
        ("Urban Tandoor","North Indian • Mughlai","Smoky kebabs and rich Indian comfort food.","Connaught Place, Delhi","20-30 min",39,199,"https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=1200&q=85"),
        ("Crust & Craft","Italian • Pizza • Pasta","Hand-stretched pizzas and silky pasta.","Saket, Delhi","25-35 min",40,249,"https://images.unsplash.com/photo-1579751626657-72bc17010498?auto=format&fit=crop&w=1200&q=85"),
        ("Bowl Theory","Healthy • Asian • Bowls","Fresh bowls and colorful ingredients.","Hauz Khas, Delhi","20-30 min",30,199,"https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=1200&q=85")]
        for n,c,d,a,t,f,m,img in data: db.session.add(Restaurant(name=n,cuisine=c,description=d,address=a,delivery_time=t,delivery_fee=f,min_order=m,image=img))
        db.session.flush()
        foods=[
        (1,"Butter Chicken","Creamy tomato gravy, tender chicken and spices",429,"Main Course",1,"https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=900&q=85"),
        (1,"Paneer Tikka","Charred paneer and peppers",329,"Starters",0,"https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=900&q=85"),
        (2,"Truffle Mushroom Pizza","Wood-fired pizza, mushrooms and mozzarella",499,"Pizza",1,"https://images.unsplash.com/photo-1579751626657-72bc17010498?auto=format&fit=crop&w=900&q=85"),
        (2,"Creamy Alfredo Pasta","Fettuccine, parmesan and herb cream",379,"Pasta",1,"https://images.unsplash.com/photo-1645112411341-6c4fd023714a?auto=format&fit=crop&w=900&q=85"),
        (3,"Teriyaki Chicken Bowl","Chicken, rice, greens and teriyaki glaze",399,"Bowls",1,"https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85"),
        (3,"Avocado Power Bowl","Avocado, greens, grains and chickpeas",349,"Bowls",0,"https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=85")]
        for rid,n,d,p,c,pop,img in foods: db.session.add(FoodItem(restaurant_id=rid,name=n,description=d,price=p,category=c,popular=bool(pop),image=img))
        db.session.add(Offer(title="50% OFF up to ₹150",code="WELCOME50",discount_type="percent",value=50,min_order=399))
        db.session.add(Offer(title="₹100 OFF on Urban Tandoor",code="TANDOOR100",restaurant_id=1,discount_type="flat",value=100,min_order=499))
    db.session.commit()

with app.app_context(): seed()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=True)

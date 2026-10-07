from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from io import BytesIO
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "rsl-electronics-cambia-esta-clave")
db_path = os.path.join(os.path.dirname(__file__), "rsl_electronics.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Producto(db.Model):
    __tablename__ = "productos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(255), nullable=True)
    descripcion = db.Column(db.String(255), nullable=True)
    categoria = db.Column(db.String(80), default="Electrodomésticos")
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

def usuario_actual():
    uid = session.get("user_id")
    return Usuario.query.get(uid) if uid else None

@app.context_processor
def inject_user():
    return {"usuario_actual": usuario_actual()}

def require_login():
    if not usuario_actual():
        flash("Debes iniciar sesión para continuar.", "error")
        return False
    return True

@app.route("/")
@app.route("/inicio (1).html")
def inicio():
    return render_template("inicio (1).html")

@app.route("/registro(4).html", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        edad = request.form.get("edad", "").strip()
        fecha_nacimiento_raw = request.form.get("fecha_nacimiento", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()
        confirmar = request.form.get("confirmar", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()

        if not all([nombre, edad, fecha_nacimiento_raw, correo, usuario, password, confirmar, telefono, direccion]):
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for("registro"))

        try:
            edad = int(edad)
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Edad o fecha inválidas.", "error")
            return redirect(url_for("registro"))

        if password != confirmar:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for("registro"))

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return redirect(url_for("registro"))

        if Usuario.query.filter((Usuario.correo == correo) | (Usuario.usuario == usuario)).first():
            flash("El correo o usuario ya existen.", "error")
            return redirect(url_for("registro"))

        nuevo = Usuario(
            nombre=nombre, edad=edad, fecha_nacimiento=fecha_nacimiento,
            correo=correo, usuario=usuario, telefono=telefono, direccion=direccion
        )
        nuevo.set_password(password)
        db.session.add(nuevo)
        db.session.commit()
        flash("Cuenta creada correctamente. Ahora inicia sesión.", "success")
        return redirect(url_for("inicio"))

    return render_template("registro(4).html")

@app.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identidad = request.form.get("identidad", "").strip().lower()
        password = request.form.get("password", "").strip()
        user = Usuario.query.filter((Usuario.correo == identidad) | (Usuario.usuario == identidad)).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Bienvenido a RSL Electronics.", "success")
            return redirect(url_for("tienda"))
        flash("Credenciales inválidas.", "error")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("inicio"))

@app.route("/internet(1) (1).html")
def tienda():
    productos = Producto.query.order_by(Producto.id.asc()).all()
    return render_template("internet(1) (1).html", productos=productos)

@app.route("/reportes/productos.pdf")
def reporte_productos():
    productos = Producto.query.order_by(Producto.id.asc()).all()
    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("RSL Electronics - Reporte de Productos", styles["Title"]),
        Spacer(1, 20),
    ]

    data = [["ID", "Nombre", "Categoría", "Precio"]]
    for producto in productos:
        data.append([
            str(producto.id),
            producto.nombre,
            producto.categoria or "General",
            f"${producto.precio:,.0f}",
        ])

    tabla = Table(data, colWidths=[40, 220, 150, 90])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d2a4d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla)
    pdf.build(story)
    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_productos.pdf"},
    )

@app.route("/admin/productos/nuevo", methods=["POST"])
def producto_nuevo():
    if not require_login():
        return redirect(url_for("inicio"))
    nombre = request.form.get("nombre", "").strip()
    precio = request.form.get("precio", "").strip()
    imagen = request.form.get("imagen", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    categoria = request.form.get("categoria", "").strip() or "Electrodomésticos"
    if not nombre or not precio:
        flash("Nombre y precio son obligatorios.", "error")
        return redirect(url_for("tienda"))
    try:
        precio = float(precio)
    except ValueError:
        flash("El precio debe ser numérico.", "error")
        return redirect(url_for("tienda"))
    db.session.add(Producto(nombre=nombre, precio=precio, imagen=imagen or None, descripcion=descripcion or None, categoria=categoria))
    db.session.commit()
    flash("Producto creado correctamente.", "success")
    return redirect(url_for("tienda"))

@app.route("/admin/productos/<int:producto_id>/editar", methods=["GET", "POST"])
def producto_editar(producto_id):
    if not require_login():
        return redirect(url_for("inicio"))
    producto = Producto.query.get_or_404(producto_id)
    if request.method == "POST":
        producto.nombre = request.form.get("nombre", "").strip()
        producto.imagen = request.form.get("imagen", "").strip() or None
        producto.descripcion = request.form.get("descripcion", "").strip() or None
        producto.categoria = request.form.get("categoria", "").strip() or "Electrodomésticos"
        try:
            producto.precio = float(request.form.get("precio", "0"))
        except ValueError:
            flash("El precio debe ser numérico.", "error")
            return redirect(url_for("producto_editar", producto_id=producto.id))
        if not producto.nombre:
            flash("El nombre es obligatorio.", "error")
            return redirect(url_for("producto_editar", producto_id=producto.id))
        db.session.commit()
        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("tienda"))
    return render_template("editar_producto.html", producto=producto)

@app.route("/admin/productos/<int:producto_id>/eliminar", methods=["POST"])
def producto_eliminar(producto_id):
    if not require_login():
        return redirect(url_for("inicio"))
    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    flash("Producto eliminado correctamente.", "info")
    return redirect(url_for("tienda"))

def seed_data():
    if Producto.query.count() == 0:
        productos = [
            {"nombre":"Nevera No Frost","precio":2500000,"imagen":"asets (2)/imagenes (2)/refrigerador.webp","descripcion":"Nevera de alta capacidad.","categoria":"Electrodomésticos"},
            {"nombre":"Lavadora Automática","precio":1800000,"imagen":"asets (2)/imagenes (2)/lavadora.avif","descripcion":"Lavadora automática eficiente.","categoria":"Electrodomésticos"},
            {"nombre":"Televisor 55 Smart TV","precio":3200000,"imagen":"asets (2)/imagenes (2)/tele.png.webp","descripcion":"Televisor inteligente de 55 pulgadas.","categoria":"Tecnología"},
            {"nombre":"Microondas Digital","precio":650000,"imagen":"asets (2)/imagenes (2)/microondas.webp","descripcion":"Microondas con panel digital.","categoria":"Electrodomésticos"},
            {"nombre":"Licuadora 6 Velocidades","precio":320000,"imagen":"asets (2)/imagenes (2)/licuadora.webp","descripcion":"Licuadora multifuncional.","categoria":"Cocina"},
            {"nombre":"Aspiradora Cyclone","precio":780000,"imagen":"asets (2)/imagenes (2)/aspiradora.jpg","descripcion":"Aspiradora de alto poder.","categoria":"Hogar"},
            {"nombre":"Cafetera Espresso","precio":420000,"imagen":"asets (2)/imagenes (2)/cafetera.jpg","descripcion":"Cafetera compacta espresso.","categoria":"Cocina"},
            {"nombre":"Aire Acondicionado 12000 BTU","precio":2200000,"imagen":"asets (2)/imagenes (2)/aire acondicionado.webp","descripcion":"Aire acondicionado para espacios medianos.","categoria":"Climatización"},
            {"nombre":"Router WiFi","precio":380000,"imagen":"asets (2)/imagenes (2)/router.jpg","descripcion":"Router de alta velocidad.","categoria":"Tecnología"},
            {"nombre":"Laptop Core i7","precio":3800000,"imagen":"asets (2)/imagenes (2)/computador.avif","descripcion":"Portátil de alto rendimiento.","categoria":"Tecnología"}
        ]
        for p in productos:
            db.session.add(Producto(**p))
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    app.run(debug=True)

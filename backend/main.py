from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import init_db, SessionLocal
from models import Temperatura, Viaje, Alerta
import datetime
import io
import os
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secreto_super_seguro")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

users = {
    "admin": {"password": "admin123", "role": "admin"},
    "usuario": {"password": "usuario123", "role": "usuario"}
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if user and user["password"] == password:
        request.session["username"] = username
        request.session["role"] = user["role"]
        if user["role"] == "admin":
            return RedirectResponse("/admin", status_code=302)
        return RedirectResponse("/usuario", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales inválidas"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    viaje = db.query(Viaje).filter(Viaje.activo == True).first()
    return templates.TemplateResponse("admin.html", {"request": request, "viaje_activo": viaje is not None})

@app.get("/admin/", response_class=HTMLResponse)
def grafico_historico(request: Request, db: Session = Depends(get_db)):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    datos = db.query(Temperatura).order_by(Temperatura.timestamp).all()
    return templates.TemplateResponse("grafico_historico.html", {"request": request, "datos": datos})

@app.get("/admin/alertas_historicas", response_class=HTMLResponse)
def alertas_historicas(request: Request, db: Session = Depends(get_db)):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    alertas = db.query(Alerta).order_by(Alerta.id.desc()).all()
    return templates.TemplateResponse("alertas_historicas.html", {"request": request, "alertas": alertas})

@app.get("/admin/reportes", response_class=HTMLResponse)
def historial_reportes(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    archivos = os.listdir("reportes") if os.path.exists("reportes") else []
    archivos_pdf = [f for f in archivos if f.endswith(".pdf")]
    return templates.TemplateResponse("historial_reportes.html", {"request": request, "reportes": archivos_pdf})

from fastapi.responses import JSONResponse

templates = Jinja2Templates(directory="templates")

@app.get("/admin/historico_temperaturas")
def mostrar_temperaturas_historicas(request: Request):
    return templates.TemplateResponse("grafico_historico.html", {"request": request})


@app.get("/admin/datos_historicos_json")
def datos_historicos_json(db: Session = Depends(get_db)):
    temperaturas = db.query(Temperatura).order_by(Temperatura.timestamp.desc()).limit(100).all()
    datos = [
        {
            "timestamp": temp.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "valor": temp.valor
        }
        for temp in temperaturas
    ]
    return JSONResponse(content=datos)




@app.get("/usuarios", response_class=HTMLResponse)
def usuarios_view(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("usuarios.html", {"request": request})

@app.get("/crear_usuario", response_class=HTMLResponse)
def crear_usuario_form(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("crear_usuario.html", {"request": request})

@app.post("/crear_usuario", response_class=HTMLResponse)
def crear_usuario(request: Request, nuevo_usuario: str = Form(...), nueva_clave: str = Form(...), nuevo_rol: str = Form(...)):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    if nuevo_usuario in users:
        return templates.TemplateResponse("crear_usuario.html", {"request": request, "error": f"El usuario '{nuevo_usuario}' ya existe."})
    users[nuevo_usuario] = {"password": nueva_clave, "role": nuevo_rol}
    return templates.TemplateResponse("crear_usuario.html", {"request": request, "mensaje": f"Usuario '{nuevo_usuario}' creado exitosamente."})

@app.get("/tabla_usuarios", response_class=HTMLResponse)
def tabla_usuarios(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("tabla_usuarios.html", {"request": request, "usuarios": users})

@app.post("/eliminar_usuario", response_class=HTMLResponse)
def eliminar_usuario(request: Request, username: str = Form(...)):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    if username in users and username != "admin":
        del users[username]
    return RedirectResponse("/tabla_usuarios", status_code=302)

@app.post("/iniciar_viaje_con_producto")
def iniciar_viaje_con_producto(request: Request, producto: str = Form(...), db: Session = Depends(get_db)):
    if request.session.get("role") not in ["admin", "usuario"]:
        return RedirectResponse("/", status_code=302)
    limites = {
        "Frutas": (7, 12),
        "Verduras": (0, 5),
        "Pescados y Mariscos": (0, 2),
        "Carnes": (0, 4),
        "Pollos": (0, 4),
    }
    if producto not in limites:
        return {"error": "Producto inválido"}
    minimo, maximo = limites[producto]
    nuevo = Viaje(producto=producto, limite_min=minimo, limite_max=maximo)
    db.add(nuevo)
    db.commit()
    return RedirectResponse("/admin" if request.session.get("role") == "admin" else "/usuario", status_code=302)

@app.post("/finalizar_viaje")
def finalizar_viaje(request: Request, db: Session = Depends(get_db)):
    if request.session.get("role") not in ["admin", "usuario"]:
        return RedirectResponse("/", status_code=302)
    viaje = db.query(Viaje).filter(Viaje.activo == True).first()
    if viaje:
        viaje.activo = False
        viaje.fin = datetime.datetime.utcnow()
        db.commit()
        temperaturas = db.query(Temperatura).filter(Temperatura.viaje_id == viaje.id).order_by(Temperatura.timestamp).all()
        alertas = db.query(Alerta).order_by(Alerta.id).all()
        usuario = request.session.get("username", "desconocido")
        pdf_buffer = generar_pdf(viaje, temperaturas, alertas, usuario)
        filename = f"reportes/reporte_{viaje.id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(filename, "wb") as f:
            f.write(pdf_buffer.getbuffer())
        pdf_buffer.seek(0)
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={os.path.basename(filename)}"})
    return RedirectResponse("/admin" if request.session.get("role") == "admin" else "/usuario", status_code=302)

@app.get("/usuario", response_class=HTMLResponse)
def usuario_view(request: Request, db: Session = Depends(get_db)):
    if request.session.get("role") != "usuario":
        return RedirectResponse("/", status_code=302)
    viaje = db.query(Viaje).filter(Viaje.activo == True).first()
    return templates.TemplateResponse("usuario.html", {"request": request, "viaje_activo": viaje is not None})

@app.get("/admin/viaje_actual", response_class=HTMLResponse)
def viaje_actual_admin(request: Request, db: Session = Depends(get_db)):
    if request.session.get("role") != "admin":
        return RedirectResponse("/", status_code=302)
    viaje = db.query(Viaje).filter(Viaje.activo == True).first()
    return templates.TemplateResponse("usuario.html", {"request": request, "viaje_activo": viaje is not None})

@app.on_event("startup")
def startup_event():
    os.makedirs("reportes", exist_ok=True)
    init_db()

def generar_pdf(viaje, temperaturas, alertas, usuario):
    buffer_pdf = io.BytesIO()
    c = canvas.Canvas(buffer_pdf, pagesize=letter)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 750, f"Reporte del viaje generado por: {usuario}")
    c.setFont("Helvetica", 11)
    c.drawString(50, 730, f"Producto: {viaje.producto}")
    c.drawString(50, 715, f"Inicio: {viaje.inicio}")
    c.drawString(50, 700, f"Fin: {viaje.fin}")
    c.drawString(50, 685, f"Límites: {viaje.limite_min}°C - {viaje.limite_max}°C")
    fig, ax = plt.subplots()
    tiempos = [t.timestamp.strftime("%H:%M:%S") for t in temperaturas]
    valores = [t.valor for t in temperaturas]
    ax.plot(tiempos, valores, marker="o", linestyle="-", color="blue")
    ax.set_title("Temperatura durante el viaje")
    ax.set_xlabel("Hora")
    ax.set_ylabel("°C")
    plt.xticks(rotation=45)
    fig.tight_layout()
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close(fig)
    img_buffer.seek(0)
    img_reader = ImageReader(img_buffer)
    c.drawImage(img_reader, 50, 400, width=500, height=200)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 370, "Alertas:")
    c.setFont("Helvetica", 10)
    y = 355
    for alerta in alertas:
        if y < 50:
            c.showPage()
            y = 750
        c.drawString(60, y, f"- {alerta.mensaje}")
        y -= 15
    c.save()
    buffer_pdf.seek(0)
    return buffer_pdf

@app.get("/temperatura_actual")
def temperatura_actual(db: Session = Depends(get_db)):
    ultima = db.query(Temperatura).order_by(Temperatura.timestamp.desc()).first()
    if ultima:
        return {"valor": ultima.valor}
    return {"valor": None}

@app.get("/viaje_activo")
def viaje_activo(db: Session = Depends(get_db)):
    viaje = db.query(Viaje).filter(Viaje.activo == True).first()
    return {"activo": viaje is not None}

@app.get("/datos_viaje_actual")
def datos_viaje_actual(db: Session = Depends(get_db)):
    viaje = db.query(Viaje).filter(Viaje.activo == True).first()
    if not viaje:
        return []
    datos = db.query(Temperatura).filter(Temperatura.viaje_id == viaje.id).order_by(Temperatura.timestamp).all()
    return [{"timestamp": d.timestamp.isoformat(), "valor": d.valor} for d in datos]

@app.get("/alertas")
def obtener_alertas(db: Session = Depends(get_db)):
    alertas = db.query(Alerta).order_by(Alerta.id.desc()).limit(20).all()
    return [{"mensaje": a.mensaje, "color": a.color or "rojo"} for a in alertas]


class TemperatureInput(BaseModel):
    valor: float

@app.post("/temperature")
def add_temperature(data: TemperatureInput, db: Session = Depends(get_db)):
    viaje = db.query(Viaje).filter(Viaje.activo == True).first()
    if not viaje:
        return {"error": "No hay viaje activo"}
    nueva = Temperatura(valor=data.valor, viaje_id=viaje.id)
    db.add(nueva)

    # Validar alertas
    if data.valor < viaje.limite_min:
        mensaje = f"Temperatura muy baja: {data.valor}°C"
        alerta = Alerta(mensaje=mensaje, viaje_id=viaje.id, color="celeste")
        db.add(alerta)
    elif data.valor > viaje.limite_max:
        mensaje = f"Temperatura muy alta: {data.valor}°C"
        alerta = Alerta(mensaje=mensaje, viaje_id=viaje.id, color="rojo")
        db.add(alerta)

    db.commit()
    return {"ok": True}

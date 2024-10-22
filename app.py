from flask import Flask, flash, render_template, request, redirect, url_for, send_file
from fpdf import FPDF
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Conectar a la base de datos
def conectar_bd():
    conexion = sqlite3.connect('facturas.db')
    cursor = conexion.cursor()

    # Crear tablas si no existen
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre_cliente TEXT,
                        dni_cliente TEXT,
                        ruc_cliente TEXT,
                        telefono_cliente TEXT,
                        direccion_cliente TEXT
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS facturas (
                        id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_cliente INTEGER,
                        fecha_emision TEXT,
                        subtotal REAL,
                        igv REAL,
                        total REAL,
                        moneda TEXT,
                        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
                        id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_factura INTEGER,
                        nombre_producto TEXT,
                        cantidad INTEGER,
                        precio REAL,
                        total REAL,
                        FOREIGN KEY (id_factura) REFERENCES facturas(id_factura)
                    )''')

    conexion.commit()
    return conexion

# Función para insertar cliente
def insertar_cliente(conexion, nombre_cliente, dni_cliente, ruc_cliente, telefono_cliente, direccion_cliente):
    cursor = conexion.cursor()
    cursor.execute('''INSERT INTO clientes (nombre_cliente, dni_cliente, ruc_cliente, telefono_cliente, direccion_cliente)
                      VALUES (?, ?, ?, ?, ?)''', (nombre_cliente, dni_cliente, ruc_cliente, telefono_cliente, direccion_cliente))
    conexion.commit()
    return cursor.lastrowid

# Función para insertar factura
def insertar_factura(conexion, id_cliente, fecha_emision, subtotal, igv, total, moneda):
    cursor = conexion.cursor()
    cursor.execute('''INSERT INTO facturas (id_cliente, fecha_emision, subtotal, igv, total, moneda)
                      VALUES (?, ?, ?, ?, ?, ?)''', (id_cliente, fecha_emision, subtotal, igv, total, moneda))
    conexion.commit()
    return cursor.lastrowid

# Función para insertar productos
def insertar_productos(conexion, id_factura, productos):
    cursor = conexion.cursor()
    for producto in productos:
        cursor.execute('''INSERT INTO productos (id_factura, nombre_producto, cantidad, precio, total)
                          VALUES (?, ?, ?, ?, ?)''', (id_factura, producto['nombre'], producto['cantidad'], producto['precio'], producto['cantidad'] * producto['precio']))
    conexion.commit()

# Función para generar el PDF de la factura
def generar_factura_pdf(nombre_cliente, dni_cliente, ruc_cliente, telefono_cliente, direccion_cliente, productos, subtotal, igv, total, moneda):
    pdf = FPDF()
    pdf.add_page()

    # Información de la empresa
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CUBA SPORT', 0, 1, 'C')  # Nombre de la empresa
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, 'RUC: 000 000 000 000 000 000 000', 0, 1, 'C')  # RUC de la empresa
    pdf.cell(0, 10, 'Teléfono: 999 999 999', 0, 1, 'C')  # Teléfono de la empresa
    pdf.ln(10)  # Salto de línea

    # Encabezado de la factura
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'FACTURA ELECTRONICA', 0, 1, 'C')
    pdf.ln(5)

    # Información del cliente
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Cliente: {nombre_cliente}", ln=True)
    pdf.cell(0, 10, f"DNI: {dni_cliente}", ln=True)
    pdf.cell(0, 10, f"RUC: {ruc_cliente}", ln=True)
    pdf.cell(0, 10, f"Teléfono: {telefono_cliente}", ln=True)
    pdf.cell(0, 10, f"Dirección: {direccion_cliente}", ln=True)
    pdf.ln(10)

    # Tabla de productos
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 10, "Producto", 1)
    pdf.cell(40, 10, "Cantidad", 1)
    pdf.cell(40, 10, "Precio", 1)
    pdf.cell(40, 10, "Total", 1)
    pdf.ln(10)

    pdf.set_font('Arial', '', 12)
    for producto in productos:
        pdf.cell(40, 10, producto['nombre'], 1)
        pdf.cell(40, 10, str(producto['cantidad']), 1)
        pdf.cell(40, 10, f"{moneda} {producto['precio']:.2f}", 1)
        pdf.cell(40, 10, f"{moneda} {producto['cantidad'] * producto['precio']:.2f}", 1)
        pdf.ln(10)

    # Totales
    pdf.ln(10)
    pdf.cell(0, 10, f"Subtotal: {moneda} {subtotal:.2f}", ln=True)
    pdf.cell(0, 10, f"IGV (18%): {moneda} {igv:.2f}", ln=True)
    pdf.cell(0, 10, f"Total a pagar: {moneda} {total:.2f}", ln=True)

    # Guardar el archivo PDF en la carpeta Facturas_Emitidas
    facturas_dir = os.path.join('static', 'Facturas_Emitidas')
    os.makedirs(facturas_dir, exist_ok=True)
    archivo_pdf = os.path.join(facturas_dir, f'factura_{nombre_cliente}.pdf')
    pdf.output(archivo_pdf)

    return archivo_pdf

@app.route('/')
def index():
    return render_template('factura.html')


@app.route('/generar_factura', methods=['POST'])
def generar_factura():
    nombre_cliente = request.form['nombre_cliente']
    dni_cliente = request.form['dni_cliente']
    ruc_cliente = request.form['ruc_cliente']
    telefono_cliente = request.form['telefono_cliente']
    direccion_cliente = request.form['direccion_cliente']
    moneda = request.form['moneda']

    # Información de productos (procesar datos)
    productos = []
    for i in range(1, 6):  # Suponiendo que hay 5 productos máximo
        nombre_producto = request.form.get(f'producto_{i}')
        cantidad = request.form.get(f'cantidad_{i}', 0, type=int)
        precio = request.form.get(f'precio_{i}', 0.0, type=float)
        if nombre_producto:
            productos.append({'nombre': nombre_producto, 'cantidad': cantidad, 'precio': precio})

    subtotal = sum(item['cantidad'] * item['precio'] for item in productos)
    igv = subtotal * 0.18
    total = subtotal + igv

    # Insertar datos en la base de datos
    conexion = conectar_bd()
    id_cliente = insertar_cliente(conexion, nombre_cliente, dni_cliente, ruc_cliente, telefono_cliente, direccion_cliente)
    id_factura = insertar_factura(conexion, id_cliente, datetime.now().strftime('%d/%m/%Y'), subtotal, igv, total, moneda)
    insertar_productos(conexion, id_factura, productos)

    # Generar y guardar la factura en PDF
    archivo_pdf = generar_factura_pdf(nombre_cliente, dni_cliente, ruc_cliente, telefono_cliente, direccion_cliente, productos, subtotal, igv, total, moneda)

    # Recargar la página del formulario principal
    return redirect(url_for('listar_facturas'))

# Listar facturas
@app.route('/facturas')
def listar_facturas():
    conexion = conectar_bd()
    cursor = conexion.cursor()

    # Obtener las facturas con los datos del cliente
    cursor.execute('''SELECT f.id_factura, c.nombre_cliente, f.fecha_emision, f.total, f.moneda
                      FROM facturas f
                      JOIN clientes c ON f.id_cliente = c.id_cliente''')
    facturas = cursor.fetchall()
    
    conexion.close()

    return render_template('lista_facturas.html', facturas=facturas)

@app.route('/eliminar_factura/<int:id_factura>', methods=['POST'])
def eliminar_factura(id_factura):
    conexion = conectar_bd()
    try:
        cursor = conexion.cursor()
        
        # Eliminar la factura y sus productos asociados
        cursor.execute('DELETE FROM productos WHERE id_factura = ?', (id_factura,))
        cursor.execute('DELETE FROM facturas WHERE id_factura = ?', (id_factura,))
        
        conexion.commit()  # Confirmar cambios
    except Exception as e:
        conexion.rollback()  # Revertir cambios en caso de error
        print(f"Error al eliminar la factura: {e}")  # Mostrar el error en la consola
    finally:
        conexion.close()  # Asegurarse de cerrar la conexión
    
    return redirect(url_for('listar_facturas'))  # Redirigir a la lista de facturas


# Descargar factura en PDF
@app.route('/descargar_factura/<int:id_factura>')
def descargar_factura(id_factura):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    # Obtener los datos de la factura y el cliente
    cursor.execute('''SELECT c.nombre_cliente, f.total
                      FROM facturas f
                      JOIN clientes c ON f.id_cliente = c.id_cliente
                      WHERE f.id_factura = ?''', (id_factura,))
    factura = cursor.fetchone()

    nombre_cliente = factura[0]

    # La ruta del archivo PDF
    archivo_pdf = os.path.join('static', 'Facturas_Emitidas', f'factura_{nombre_cliente}.pdf')

    # Descargar el archivo
    return send_file(archivo_pdf, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

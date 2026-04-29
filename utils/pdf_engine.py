import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_pdf_catalogue(df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("<b>CATALOGUE PRODUITS - PHARMACIEL PRO</b>", styles['Title']))
    elements.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    style_p = styles["Normal"]
    style_p.fontSize = 9
    
    data = [["Produit", "Laboratoire", "Famille", "PPA"]]
    for _, row in df.iterrows():
        p_name = Paragraph(f"<b>{row['Produit']}</b>", style_p)
        p_lab = Paragraph(str(row['Laboratoire']), style_p)
        p_fam = Paragraph(str(row['Famille']), style_p)
        p_price = Paragraph(f"<b>{row['PPA']} DA</b>", style_p)
        data.append([p_name, p_lab, p_fam, p_price])
        
    t = Table(data, colWidths=[230, 110, 110, 85])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.cadetblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_promo_flyer(df):
    df_promo = df[df['Promo'] == True]
    if df_promo.empty: return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = styles['Title']
    title_style.textColor = colors.red
    title_style.fontSize = 24
    
    elements.append(Paragraph(f"<b>🔥 OFFRES SPÉCIALES PROMO 🔥</b>", title_style))
    elements.append(Paragraph(f"PHARMACIEL PRO - Profitez de nos meilleures remises !", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    style_p = styles["Normal"]
    style_p.fontSize = 11
    
    data = [[Paragraph("<b>Produit</b>", style_p), Paragraph("<b>Laboratoire</b>", style_p), Paragraph("<b>Prix PROMO</b>", style_p)]]
    for _, row in df_promo.iterrows():
        p_name = Paragraph(f"<b>{row['Produit']}</b>", style_p)
        p_lab = Paragraph(str(row['Laboratoire']), style_p)
        p_price = Paragraph(f"<font color='red' size=12><b>{row['PPA']} DA</b></font>", style_p)
        data.append([p_name, p_lab, p_price])
        
    t = Table(data, colWidths=[250, 150, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.red),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.red),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_invoice(cart_dict, total_val):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("<b>FACTURE PROFORMA - PHARMACIEL PRO</b>", styles['Title']))
    elements.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    data = [["Désignation", "Prix Unitaire", "Qté", "Total"]]
    for k, v in cart_dict.items():
        data.append([k, f"{v['price']} DA", v['qty'], f"{v['price']*v['qty']} DA"])
    data.append(["", "", "<b>TOTAL</b>", f"<b>{total_val} DA</b>"])
    
    t = Table(data, colWidths=[250, 100, 50, 100])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

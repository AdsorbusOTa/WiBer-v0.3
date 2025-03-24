# -*- coding: utf-8 -*-
"""
Created on Thu Mar 20 19:12:26 2025

@author: otamm
"""

import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
import os

# deutsches Zahlenformat festlegen
def format_de(value, decimals=2, tausender="'"):
    """
    Formatiert eine Zahl im deutschen Format mit optionalem Tausendertrennzeichen.
    Beispiel: 1234567.89 → 1'234'567,89 (bei tausender="'")
    """
    if isinstance(value, (int, float)):
        s = f"{value:,.{decimals}f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", tausender)
        return s
    return str(value)

# Sicherstellen, dass der Speicherordner existiert
if not os.path.exists("datenbank"):
    os.makedirs("datenbank")

db_path = "datenbank/betriebsdaten.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tabelle erstellen
cursor.execute('''
    CREATE TABLE IF NOT EXISTS betriebsdaten (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        standort TEXT,
        betreiber TEXT,
        kontaktperson TEXT,
        email TEXT,
        telefon TEXT,
        anschrift TEXT,
        stromverbrauch REAL,
        betriebsstunden INTEGER,
        strompreis REAL,
        max_kälteleistung REAL,
        durchschn_kälteleistung REAL,
        wirkungsgrad REAL,
        volumenstrom REAL,
        temp_eintritt REAL,
        temp_austritt REAL,
        kosten REAL
    )
''')
conn.commit()

def generate_pdf(data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Betriebsdaten-Bericht", ln=True, align="C")
    pdf.ln(10)
    for key, value in data.items():
        pdf.cell(200, 10, f"{key}: {value}", ln=True)
    pdf_path = "Betriebsbericht.pdf"
    pdf.output(pdf_path)
    return pdf_path

# Web-App UI
st.title("Betriebsdatenerfassung für die Kältemaschine")

# Auswahl eines vorhandenen Datensatzes
cursor.execute("SELECT id, standort FROM betriebsdaten ORDER BY id DESC")
datensatz_auswahl = cursor.fetchall()

# Standarddatensatz sicherstellen (einmalig anlegen, falls nicht vorhanden)
cursor.execute("SELECT COUNT(*) FROM betriebsdaten WHERE standort = 'Standard'")
if cursor.fetchone()[0] == 0:
    cursor.execute('''
        INSERT INTO betriebsdaten (
            standort, betreiber, kontaktperson, email, telefon, anschrift,
            stromverbrauch, betriebsstunden, strompreis,
            max_kälteleistung, durchschn_kälteleistung, wirkungsgrad,
            volumenstrom, temp_eintritt, temp_austritt, kosten
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Standard', 'Muster GmbH', 'Martina Mustermann', 'martina.mustermann@mustergmbh.com', '+49 123 12345678', 'Musterstrasse 1 12345 Musterstadt',
        200000.0, 6000, 0.32,
        120.0, 100.0, 3.0,
        28.7, 18.0, 15.0, 200000.0 * 0.32
    ))
    conn.commit()

auswahl_id = None
if datensatz_auswahl:
    optionen = {f"ID {row[0]} - {row[1]}": row[0] for row in datensatz_auswahl}
    auswahl_label = st.selectbox("Vorhandenen Datensatz laden:", list(optionen.keys()))
    auswahl_id = optionen[auswahl_label]

# Datensatz laden, wenn gewählt – oder 'Standard'-Datensatz beim Start
if auswahl_id:
    cursor.execute("SELECT * FROM betriebsdaten WHERE id = ?", (auswahl_id,))
    eintrag = cursor.fetchone()
else:
    cursor.execute("SELECT * FROM betriebsdaten WHERE standort = 'Standard' LIMIT 1")
    eintrag = cursor.fetchone()


# Robustere Zuweisung mit Fallback-Werten für Textfelder
(
    _, standort_val, betreiber_val, kontaktperson_val, email_val, telefon_val, anschrift_val,
    stromverbrauch_val, betriebsstunden_val, strompreis_val,
    max_kälteleistung_val, durchschn_kälteleistung_val, wirkungsgrad_val,
    volumenstrom_val, temp_eintritt_val, temp_austritt_val, _
) = eintrag if eintrag else (None, None, None, None, None, None, None,
                              None, None, None,
                              None, None, None,
                              None, None, None, None)

standort_val = standort_val or ""
betreiber_val = betreiber_val or ""
kontaktperson_val = kontaktperson_val or ""
email_val = email_val or ""
telefon_val = telefon_val or ""
anschrift_val = anschrift_val or ""

stromverbrauch_val = stromverbrauch_val if stromverbrauch_val is not None else 200000.0
betriebsstunden_val = betriebsstunden_val if betriebsstunden_val is not None else 6000
strompreis_val = strompreis_val if strompreis_val is not None else 0.3
max_kälteleistung_val = max_kälteleistung_val if max_kälteleistung_val is not None else 120.0
durchschn_kälteleistung_val = durchschn_kälteleistung_val if durchschn_kälteleistung_val is not None else 100.0
wirkungsgrad_val = wirkungsgrad_val if wirkungsgrad_val is not None else 3.0
volumenstrom_val = volumenstrom_val if volumenstrom_val is not None else 28.7
temp_eintritt_val = temp_eintritt_val if temp_eintritt_val is not None else 18.0
temp_austritt_val = temp_austritt_val if temp_austritt_val is not None else 15.0

# Schrittweite definieren für bessere Nutzung mit Plus-/Minus-Schaltflächen
stromverbrauch_step = 50.0
betriebsstunden_step = 100
messung_step = 0.5
strompreis_step = 0.01
leistung_step = 5.0
eer_step = 0.1
temp_step = 0.5
volumen_step = 0.5

st.header("1. Allgemeine Informationen")
standort = st.text_input("Standort der Anlage", value=standort_val)
betreiber = st.text_input("Betreiber / Unternehmen", value=betreiber_val)
kontaktperson = st.text_input("Kontaktperson", value=kontaktperson_val)
email = st.text_input("E-Mail-Adresse", value=email_val)
telefon = st.text_input("Telefonnummer", value=telefon_val)
anschrift = st.text_area("Anschrift", value=anschrift_val)


st.header("2. Energieverbrauch & Kosten")
st.markdown(
    """
    <style>
    .custom-info-box {
        padding: 1em;
        background-color: #172D43; /* Exakte Info-Box-Farbe */
        color: #C7EBFF; /* Weiße Schrift für besseren Kontrast */
        border-radius: 5px;
        font-weight: normal;
    }
    </style>
    <div class="custom-info-box">
        💡 Geben Sie hier bitte den jährlichen Stromverbrauch Ihrer Kältemaschine in kWh 
        und die erfassten Betriebsstunden an.<br><br>
        Falls diese Werte nicht vorliegen, können Sie in <strong>2.1</strong> 
        über eine Kurzzeitmessung eine Prognose erstellen.
    </div>
    """,
    unsafe_allow_html=True
)



stromverbrauch = st.number_input("Jahresstromverbrauch der Kältemaschine (kWh)", min_value=0.0, value=stromverbrauch_val, step=stromverbrauch_step, format="%0.0f")
betriebsstunden = st.number_input("Betriebsstunden pro Jahr", min_value=0, max_value=8760, value=betriebsstunden_val, step=betriebsstunden_step, format="%d")
st.info("💡 Ihren Strompreis finden Sie auf Ihrer Stromrechnung.")
strompreis = st.number_input("Strompreis pro kWh (EUR)", min_value=0.0, value=strompreis_val, step=strompreis_step, format="%0.2f")

st.subheader("2.1 Messbasierte Verbrauchserfassung (optional)")
st.info("💡 Falls Sie einen Stromzähler verwenden, können Sie hier einen gemessenen Wert für die Kältemaschine eintragen.")

messverbrauch = st.number_input("Gemessener Stromverbrauch (kWh)", min_value=0.0, step=stromverbrauch_step, format="%0.0f")
messdauer = st.number_input("Dauer der Messung (Stunden)", min_value=0.5, step=messung_step, format="%0.1f")

# Berechnung
if messdauer > 0:
    leistung_messung = messverbrauch / messdauer
    st.write(f"🔹 Durchschnittliche elektrische Leistungsaufnahme: {format_de(leistung_messung, 0)} kW")
    berechnete_kaelteleistung = leistung_messung * wirkungsgrad_val
    st.write(f"🔹 resutierende durchschnittliche Kälteleistung: {format_de(berechnete_kaelteleistung, 1)} kW")

    if betriebsstunden > 0:
        jahresverbrauch = leistung_messung * betriebsstunden
        st.write(f"🔹 Jahresstromverbrauch (prognostiziert): {format_de(jahresverbrauch, 0)} kWh")



st.header("3. Daten der Bestandskältemaschine")
st.info("💡 Maximale Kälteleistung laut Hersteller. Durchschnittswerte können geschätzt oder berechnet werden.")
max_kälteleistung = st.number_input("Maximale Kälteleistung (kW)", min_value=0.0, value=max_kälteleistung_val, step=leistung_step, format="%0.1f")
durchschn_kälteleistung = st.number_input("Durchschnittliche Kälteleistung (kW, falls bekannt)", min_value=0.0, value=durchschn_kälteleistung_val, step=leistung_step, format="%0.1f")
wirkungsgrad = st.number_input("Wirkungsgrad (EER)", min_value=0.1, max_value=10.0, value=wirkungsgrad_val, step=eer_step, format="%0.1f")

# Berechnung: Durchschnittliche Kälteleistung aus Stromverbrauch und Wirkungsgrad
if wirkungsgrad > 0:
    berechnete_kälteleistung = stromverbrauch  /betriebsstunden * wirkungsgrad
    st.write(f"🔹 Berechnete durchschnittliche Kälteleistung: {format_de(berechnete_kälteleistung, 1)} kW")

    # Vergleich mit Nutzereingabe
    if durchschn_kälteleistung > 0:
        differenz = abs(durchschn_kälteleistung - berechnete_kälteleistung)
        prozent_diff = differenz / berechnete_kälteleistung

        if prozent_diff < 0.05:
            st.success(f"✅ Unterschied zur Eingabe: {format_de(differenz, 1)} kW ({prozent_diff:.0%} Abweichung)")
        elif prozent_diff < 0.20:
            st.warning(f"⚠️ Unterschied zur Eingabe: {format_de(differenz, 1)} kW ({prozent_diff:.0%} Abweichung)")
        else:
            st.error(f"🚨 Starke Abweichung: {format_de(differenz, 1)} kW ({prozent_diff:.0%} Abweichung)")


st.header("4. Alternative Leistungsberechnung")
st.info("💡 Volumenstrom in m³/h und Temperaturen an Ein- und Austritt zur Berechnung der Leistung.")
volumenstrom = st.number_input("Volumenstrom (m³/h)", min_value=0.0, value=5.0, step=volumen_step, format="%0.1f")
temp_eintritt = st.number_input("Eintrittstemperatur (°C)", min_value=8.0, max_value=30.0, value=18.0, step=temp_step, format="%0.1f")
temp_austritt = st.number_input("Austrittstemperatur (°C)", min_value=4.0, max_value=25.0, value=15.0, step=temp_step, format="%0.1f")

delta_T = temp_eintritt - temp_austritt if temp_eintritt > temp_austritt else 0
leistung_temp = volumenstrom * 1.16 * delta_T if delta_T > 0 and volumenstrom > 0 else 0

if betriebsstunden > 0:
    kosten = stromverbrauch * strompreis
    st.write(f"🔹 **Jährliche Stromkosten:** {format_de(kosten, 0)} EUR")
else:
    kosten = None

if st.button("Daten speichern"):
    cursor.execute('''
        INSERT INTO betriebsdaten (
            standort, betreiber, kontaktperson, email, telefon, anschrift,
            stromverbrauch, betriebsstunden, strompreis,
            max_kälteleistung, durchschn_kälteleistung, wirkungsgrad,
            volumenstrom, temp_eintritt, temp_austritt,
            kosten
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        standort, betreiber, kontaktperson, email, telefon, anschrift,
        stromverbrauch, betriebsstunden, strompreis,
        max_kälteleistung, durchschn_kälteleistung, wirkungsgrad,
        volumenstrom, temp_eintritt, temp_austritt,
        kosten
    ))
    conn.commit()
    st.success("✅ Daten wurden erfolgreich gespeichert!")

if st.button("Gespeicherte Daten anzeigen"):
    cursor.execute("SELECT * FROM betriebsdaten")
    daten = cursor.fetchall()
    df = pd.DataFrame(daten, columns=[
        "ID", "Standort", "Betreiber", "Kontaktperson", "E-Mail", "Telefon", "Anschrift",
        "Stromverbrauch", "Betriebsstunden", "Strompreis", "Max. Kälteleistung",
        "Durchschn. Kälteleistung", "Wirkungsgrad", "Volumenstrom",
        "T Eintritt", "T Austritt", "Kosten"
    ])
    st.dataframe(df)

if st.button("PDF erstellen"):
    data = {
        "Standort": standort,
        "Betreiber": betreiber,
        "Kontaktperson": kontaktperson,
        "E-Mail": email,
        "Telefon": telefon,
        "Stromverbrauch (kWh)": format_de(stromverbrauch, 0),
        "Betriebsstunden": format_de(betriebsstunden, 0),
        "Strompreis (EUR/kWh)": format_de(strompreis, 2),
        "Max. Kälteleistung (kW)": format_de(max_kälteleistung, 0),
        "Durchschn. Kälteleistung (kW)": format_de(durchschn_kälteleistung, 0),
        "Wirkungsgrad (EER)": format_de(wirkungsgrad, 1),
        "Volumenstrom (m³/h)": format_de(volumenstrom, 1),
        "Temperatur Eintritt (°C)": format_de(temp_eintritt, 1),
        "Temperatur Austritt (°C)": format_de(temp_austritt, 1),
        "Jährliche Kosten (EUR)": format_de(kosten, 0) if kosten is not None else "N/A",
    }
    pdf_path = generate_pdf(data)
    st.success("✅ PDF wurde erstellt!")
    with open(pdf_path, "rb") as file:
        st.download_button("📄 PDF herunterladen", file, file_name="Betriebsbericht.pdf")
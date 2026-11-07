import streamlit as st, pandas as pd, numpy as np, sqlite3, re
from pathlib import Path
from datetime import date
import pdfplumber
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

ROOT=Path(__file__).parent; DB=ROOT/'data'/'cvi_ia.db'
st.set_page_config(page_title='CVI-IA',page_icon='⚡',layout='wide')
st.markdown('''<style>.stApp{background:#f4f7f8}h1,h2,h3{color:#153B5B}div[data-testid="stMetric"]{background:white;border:1px solid #e2e8ec;padding:12px;border-radius:12px}div.stButton>button,div.stDownloadButton>button{background:#159A79;color:white;border:0}</style>''',unsafe_allow_html=True)

def db(sql,args=(),read=False):
    DB.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS energia(id INTEGER PRIMARY KEY,folio TEXT,fecha TEXT,kwh REAL,importe REAL,dias INTEGER,personas INTEGER,temperatura REAL,area REAL,prediccion REAL,alerta INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS agua(id INTEGER PRIMARY KEY,fecha TEXT,inicial REAL,final REAL,horas REAL,sin_uso INTEGER)''')
        if read:return pd.read_sql_query(sql,c,params=args)
        c.execute(sql,args); c.commit()

def modelito():
    rng=np.random.default_rng(42); n=4000
    p=rng.integers(1,8,n); d=rng.integers(27,34,n); t=rng.normal(22,5,n).clip(8,39); m=rng.integers(1,13,n); a=rng.normal(75,28,n).clip(30,220)
    y=(42+p*27+a*.55+np.maximum(t-23,0)*7.5)*(d/30)*(1+.1*np.sin((m-1)*2*np.pi/12))+rng.normal(0,18,n)
    X=pd.DataFrame({'personas':p,'dias':d,'temperatura':t,'mes':m,'area':a})
    model=make_pipeline(StandardScaler(),MLPRegressor(hidden_layer_sizes=(32,16),max_iter=400,early_stopping=True,random_state=42)); model.fit(X,y)
    return model,mean_absolute_error(y,model.predict(X))

@st.cache_resource
def trained():return modelito()
def mxn(x):return f'${x:,.2f} MXN'
def pdfread(f):
    try:
        with pdfplumber.open(f) as pdf:return '\n'.join(p.extract_text() or '' for p in pdf.pages)
    except:return ''
def parse(txt):
    out={}
    for key,pat in [('kWh',r'([\d,]+)\s*kwh'),('importe',r'(?:total\s*a\s*pagar|importe\s*a\s*pagar|a\s*pagar)\s*[:$\s]*([\d,]+(?:\.\d{1,2})?)')]:
        m=re.search(pat,txt,re.I)
        if m:
            try:out[key]=float(m.group(1).replace(',',''))
            except:pass
    return out

st.title('⚡ CVI-IA')
st.subheader('Calculadora de Viabilidad, Consumo y Ahorro Inteligente')
st.write('Analiza el consumo, estima escenarios de ahorro y detecta cambios inusuales. El prototipo prioriza hogares y está preparado para ampliarse a grandes instalaciones.')
with st.sidebar:
    st.header('Acceso comunitario')
    st.write('Quien no tenga internet o computadora puede acudir a un módulo participante o solicitar captura asistida por teléfono.')
    st.caption('Prototipo académico. No afiliado a CFE ni a organismos de agua.')

T=st.tabs(['🏠 Calculadora','📄 Recibo PDF','📈 Historial','💧 Agua','🏢 Grandes instalaciones','🤝 Comunidad'])
with T[0]:
    st.header('Calculadora del hogar')
    c1,c2,c3=st.columns(3)
    kwh=c1.number_input('Consumo del periodo (kWh)',0.,100000.,300.,10.)
    importe=c2.number_input('Importe del recibo (MXN)',0.,1000000.,850.,50.)
    dias=c3.number_input('Días del periodo',1,120,60)
    c1,c2,c3=st.columns(3)
    personas=c1.number_input('Personas en el hogar',1,20,3)
    temp=c2.number_input('Temperatura promedio (°C)',-5.,50.,22.)
    area=c3.number_input('Área aproximada de vivienda (m²)',10.,1000.,75.)
    folio=st.text_input('Folio o alias opcional (no escribas nombre completo)')
    pct=st.slider('Escenario hipotético de ahorro',0,30,10,5)
    mdl,mae=trained(); X=pd.DataFrame([{'personas':personas,'dias':dias,'temperatura':temp,'mes':date.today().month,'area':area}]); esperado=max(0,float(mdl.predict(X)[0]))
    desv=(kwh-esperado)/esperado*100 if esperado else 0; alerta=desv>30
    a,b,c,d=st.columns(4); a.metric('Consumo diario',f'{kwh/dias:.2f} kWh'); b.metric('Costo promedio',mxn(importe/kwh) if kwh else 'N/D'); c.metric('Ahorro hipotético',mxn(importe*pct/100)); d.metric('Predicción orientativa',f'{esperado:.0f} kWh')
    if alerta:st.warning(f'Consumo {desv:.0f}% por encima de la referencia demostrativa. Revisa las condiciones; no prueba una falla.')
    else:st.info('No se activa la alerta demostrativa. Comparar varios recibos permite observar mejor las tendencias.')
    st.caption(f'MLP entrenada con datos sintéticos. MAE en esos datos: {mae:.1f} kWh. No es validación con hogares reales.')
    recs=['Compara periodos de duración y temporada similares.','Revisa equipos que permanecen encendidos sin necesidad.','Da mantenimiento a refrigeradores y equipos de climatización.','No desconectes equipos médicos, de seguridad ni elementos necesarios para el bienestar.']
    if alerta:recs.insert(0,'Verifica cambios en clima, ocupación, días facturados y equipos antes de atribuir el aumento a una anomalía.')
    st.subheader('Recomendaciones')
    for r in recs:st.write('• '+r)
    if st.button('Guardar consumo en SQLite'):
        if kwh<=0 or importe<=0:st.error('Captura consumo e importe mayores que cero.')
        else:
            db('INSERT INTO energia(folio,fecha,kwh,importe,dias,personas,temperatura,area,prediccion,alerta) VALUES(?,?,?,?,?,?,?,?,?,?)',(folio or 'Hogar',date.today().isoformat(),kwh,importe,dias,personas,temp,area,esperado,int(alerta)))
            st.success('Registro guardado en la base de datos local.')
    reporte=f'CVI-IA | REPORTE DE ORIENTACIÓN\nFecha: {date.today()}\nConsumo: {kwh} kWh\nImporte: {mxn(importe)}\nDías: {dias}\nPredicción orientativa: {esperado:.1f} kWh\nAhorro hipotético: {mxn(importe*pct/100)}\nAlerta: {alerta}\n\n'+ '\n'.join('- '+r for r in recs)+'\n\nNo confirma fugas ni garantiza ahorros. Modelo entrenado con datos sintéticos.'
    st.download_button('Descargar reporte',reporte,'reporte_CVI_IA.txt','text/plain')
with T[1]:
    st.header('Análisis de recibo PDF'); f=st.file_uploader('Carga un recibo PDF con texto seleccionable',type=['pdf'])
    if f:
        txt=pdfread(f)
        if txt:
            st.text_area('Texto extraído: verifica la información',txt[:7000],height=180); parsed=parse(txt)
            if parsed:st.json(parsed); st.info('Confirma los valores y transcríbelos en la calculadora. La extracción puede equivocarse.')
            else:st.warning('No se reconocieron kWh o importe; captura los datos manualmente.')
        else:st.warning('No se pudo leer texto. Si el PDF es una imagen escaneada, será necesario OCR o captura manual.')
    st.caption('No cargues recibos de otras personas sin autorización. El PDF no se guarda en la base de datos.')
with T[2]:
    st.header('Historial guardado'); hist=db('SELECT * FROM energia ORDER BY id DESC',read=True)
    if hist.empty:st.info('Todavía no hay registros. Guarda un consumo desde la calculadora.')
    else:
        st.dataframe(hist,use_container_width=True,hide_index=True); st.line_chart(hist.sort_values('id').set_index('fecha')['kwh']); st.download_button('Exportar historial CSV',hist.to_csv(index=False).encode('utf-8-sig'),'historial_CVI_IA.csv','text/csv')
with T[3]:
    st.header('Agua: posible flujo no esperado'); st.write('Compara lecturas del medidor, idealmente durante un periodo sin uso.')
    a,b,c=st.columns(3); ini=a.number_input('Lectura inicial (m³)',0.,1000000.,120.,.1); fin=b.number_input('Lectura final (m³)',0.,1000000.,120.8,.1); horas=c.number_input('Horas entre lecturas',1.,168.,8.)
    sinuso=st.checkbox('No se utilizó agua durante ese periodo')
    if fin<ini:st.error('La lectura final no puede ser menor que la inicial.')
    else:
        dif=fin-ini; st.metric('Agua registrada',f'{dif:.2f} m³'); st.metric('Flujo promedio',f'{dif*1000/horas:.1f} litros/hora')
        if sinuso and dif>0:st.warning('El medidor avanzó durante un periodo declarado sin uso. Podría haber fuga o consumo no identificado; solicita revisión si se repite.')
        elif dif>0:st.info('Repite la medición durante un periodo sin uso para investigar flujo continuo.')
        else:st.success('No se observó incremento entre estas lecturas.')
        if st.button('Guardar lecturas de agua'):db('INSERT INTO agua(fecha,inicial,final,horas,sin_uso) VALUES(?,?,?,?,?)',(date.today().isoformat(),ini,fin,horas,int(sinuso))); st.success('Lectura guardada.')
    st.caption('La alerta no confirma una fuga: puede haber errores de lectura o consumos inadvertidos.')
with T[4]:
    st.header('Preparado para centros de datos y aeropuertos'); tipo=st.selectbox('Tipo de instalación',['Centro de datos','Aeropuerto','Hospital','Escuela','Edificio público'])
    a,b,c=st.columns(3); a.number_input('Energía del periodo (kWh)',0.,1e9,25000.); b.number_input('Agua del periodo (m³)',0.,1e8,180.); c.number_input('Temperatura (°C)',-5.,60.,25.)
    a,b,c=st.columns(3); a.number_input('Ocupación/personas',0,1000000,500); b.number_input('Horas de operación al día',1,24,16); c.number_input('Número de zonas',1,10000,5)
    st.info(f'Perfil {tipo}: formulario de captura preparado. Aún no predice para instalaciones grandes; requiere datos históricos específicos y autorizados.')
    st.write('Variables futuras: fecha/hora, zona, carga de equipos, presión y caudal, humedad, temperatura interior, actividad, superficie y mantenimiento.')
with T[5]:
    st.header('Módulo comunitario y atención telefónica'); st.markdown('''1. La persona acude con su recibo o dicta datos por teléfono.\n2. El personal explica el uso de la información y solicita autorización.\n3. Captura consumo, importe y periodo.\n4. Entrega o explica el reporte.\n5. Aclara que las alertas no confirman fugas.\n6. En otro contacto compara el siguiente recibo.''')
    with st.form('captura_comunidad'):
        f=st.text_input('Folio o iniciales (evita nombre completo)'); ck=st.number_input('Consumo kWh',0.,100000.,0.); ca=st.number_input('Importe MXN',0.,1000000.,0.); cd=st.number_input('Días del periodo',1,120,60); ok=st.checkbox('La persona autorizó el uso de estos datos'); enviar=st.form_submit_button('Guardar ficha')
    if enviar:
        if not ok or ck<=0 or ca<=0:st.error('Se requiere autorización y datos mayores que cero.')
        else:db('INSERT INTO energia(folio,fecha,kwh,importe,dias) VALUES(?,?,?,?,?)',(f or 'Captura comunitaria',date.today().isoformat(),ck,ca,cd)); st.success('Ficha guardada. No se almacena teléfono ni nombre completo.')
    st.caption('La atención telefónica real requiere personal, capacitación, acuerdos y protocolo de privacidad. Este prototipo no realiza llamadas.')
st.divider(); st.caption('CVI-IA es un prototipo académico. No sustituye a CFE, al organismo de agua ni a personal técnico. Ahorros estimados no son garantías.')

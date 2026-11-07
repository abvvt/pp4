# CVI-IA — ZIP listo para ejecutar

## Incluye
- `app.py`: interfaz web y lógica principal.
- `database.py`: punto de extensión para funciones de base de datos.
- `requirements.txt`: dependencias Python.
- `run_windows.bat`: instalación y arranque en Windows.
- `run_mac_linux.sh`: instalación y arranque en macOS/Linux.
- `data/`: aquí se crea automáticamente `cvi_ia.db` (SQLite) al guardar el primer registro.

## Requisitos
Python 3.10 o superior y conexión a internet durante la primera instalación.

## Windows
1. Descomprime el ZIP.
2. Abre la carpeta `CVI_IA_Listo`.
3. Haz doble clic en `run_windows.bat`.
4. Espera la instalación. Si no se abre el navegador, visita `http://localhost:8501`.

## macOS/Linux
Abre terminal en la carpeta y ejecuta `./run_mac_linux.sh`.

## ¿Por qué no hay HTML/JavaScript separados?
Streamlit genera la interfaz web desde Python y ya proporciona formularios, tablas, gráficas y botones. Se utiliza CSS para el diseño. Separar un frontend HTML/JavaScript no es necesario para este prototipo y aumentaría la complejidad. Se puede incorporar en una etapa posterior.

## Base de datos
Se utiliza SQLite, que no necesita servidor ni instalación adicional. El archivo `data/cvi_ia.db` se genera automáticamente al guardar registros. Haz una copia de ese archivo para respaldar la información.

## Limitaciones importantes
- La red neuronal MLP se entrena con datos sintéticos; no son datos reales de CFE ni referencia oficial.
- La predicción es demostrativa, no debe usarse para sanciones, cortes ni decisiones sobre apoyos.
- La lectura de PDF funciona con texto seleccionable y patrones reconocibles; recibos escaneados requieren OCR o captura manual.
- El movimiento del medidor durante un periodo sin uso puede indicar consumo no identificado, pero no confirma una fuga.
- La pestaña de centros de datos/aeropuertos prepara la captura; requiere datos históricos específicos antes de predecir.
- El módulo comunitario guarda folio y consumo con autorización; no realiza llamadas ni almacena teléfonos.

## Próximas etapas
Conseguir datos reales voluntarios, autorizados y anonimizados; comparar MLP con regresión y Random Forest; evaluar MAE/RMSE y falsos positivos; incorporar OCR y diseñar el protocolo comunitario.

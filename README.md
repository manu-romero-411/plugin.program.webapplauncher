# WebApp Launcher (Kodi addon)

Addon de tipo "program" (`xbmc.python.pluginsource`, `provides="executable"`)
para Kodi con Python 3. Lee una carpeta con ficheros `.webapp` y los lista
como un menú, con carátula, favoritos y acceso desde temas.

## Estructura esperada de la carpeta de lanzadores

```
mis_launchers/
├── youtube.webapp
├── otra_app.webapp
└── app-icons/
    ├── youtube.png      # 600x900, o el tamaño/formato que prefieras
    └── otra_app.jpg
```

- La carátula se busca por **nombre de fichero** (sin extensión) dentro de
  `app-icons/` (configurable), probando `.png`, `.jpg`, `.jpeg`, `.webp` en
  ese orden. Si no hay carátula, se usa el icono del addon.
- El identificador estable de cada lanzador (usado en la URL de favoritos
  y accesos de tema) es también el **nombre de fichero**, no el `name` del
  ini.

### Formato de los `.webapp`

Fichero tipo ini con una única sección `[kodi_webapp]`:

```ini
[kodi_webapp]
name=YouTube
custom_command=/usr/bin/firefox %URL%
url=https://www.youtube.com
```

- **`url`** (obligatorio): si falta o está vacío, el lanzador **no se
  muestra** en el menú (se descarta silenciosamente).
- **`name`** (opcional): etiqueta mostrada. Si falta o está vacío, se usa
  el nombre de fichero (embellecido si `prettify_labels` está activo,
  p.ej. `mi_cool_app` → `Mi Cool App`).
- **`custom_command`** (opcional): si está definido, **sustituye por
  completo** al script global configurado en ajustes para ese lanzador
  concreto. Admite los tokens `%WEBAPP%` (ruta absoluta al `.webapp`) y
  `%URL%` (valor del campo `url`), sustituidos en cada argumento tras
  tokenizar la línea respetando comillas — así que rutas o URLs con
  espacios funcionan bien aunque vayan sin comillas en el propio token,
  por ejemplo:
  ```ini
  custom_command="/opt/mi app/launcher.sh" --file %WEBAPP% --url="%URL%"
  ```
  Si `custom_command` no está definido (o está vacío), el `.webapp` se
  pasa como único argumento al script global (`script /ruta/al/archivo.webapp`,
  equivalente a un `%WEBAPP%` implícito).
- Ficheros sin la sección `[kodi_webapp]`, o que no sean un ini válido,
  se ignoran (se registra un aviso en el log de Kodi, pero no rompen el
  listado del resto).
- El nombre de la sección se compara sin distinguir mayúsculas
  (`[KODI_WEBAPP]` también vale); los espacios alrededor del `=` se
  ignoran.

## Ajustes del addon

- **Launchers folder**: carpeta con los `.webapp`. Si no está configurada,
  la primera vez que abras el addon se te pedirá elegirla con un selector
  de carpetas (también se puede cambiar luego desde Ajustes).
- **Icons subfolder name**: subcarpeta de carátulas (`app-icons` por
  defecto).
- **Executor script**: script ejecutable global (bash, python...) que
  Kodi invocará como `script /ruta/completa/al/archivo.webapp` para
  cualquier `.webapp` que **no** defina `custom_command`. Debe tener
  permiso de ejecución (`chmod +x`). Si todos tus `.webapp` usan
  `custom_command`, no hace falta configurarlo.
- **Prettify labels**: activa/desactiva el embellecido de nombres.
- **Minimize Kodi while a launcher is running**: minimiza Kodi antes de
  lanzar (útil en setups de una sola GPU/monitor).
- **Wait for the launcher to exit**: si se activa, Kodi espera a que el
  proceso termine antes de continuar (útil si quieres encadenar acciones
  o si tu script hace limpieza al cerrar); si no, se lanza en segundo
  plano y Kodi sigue funcionando con normalidad.

Ver `examples/run-webapp.sh` como punto de partida para el script
ejecutor.

## Favoritos

Cada elemento del listado es un ítem normal de Kodi (no una carpeta), así
que el menú contextual estándar de Kodi ("Add to favourites") funciona
sin nada adicional por parte del addon.

## Uso desde temas (accesos directos)

Cada lanzador tiene una URL estable:

```
plugin://plugin.program.webapplauncher/?action=run&name=<nombre_sin_extension>
```

Puedes apuntar un botón/widget del tema directamente a esa URL con
`RunPlugin(...)` o `ActivateWindow(...)` según lo que soporte el skin, sin
depender de que el usuario navegue el listado completo.

## Instalación

1. Copia la carpeta `plugin.program.webapplauncher` a
   `~/.kodi/addons/` (o usa "Install from zip file" con el zip
   generado).
2. Reinicia Kodi o refresca los addons.
3. Añade el programa al menú, ábrelo, configura la carpeta y el script.

## Notas de desarrollo

- Código en Python 3, pensado para el Python 3 nativo de Kodi (Matrix en
  adelante).
- Comentarios, docstrings y mensajes de log en inglés; textos de la UI
  localizados vía `strings.po` (inglés + español incluidos).
- `pylint` sobre `resources/lib/*.py` y `default.py`: 10.00/10.

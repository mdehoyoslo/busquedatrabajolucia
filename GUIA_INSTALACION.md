# Radar Lucía — instalación (dos móviles + ordenador + búsqueda diaria)

Esta es una aplicación PWA estática con Supabase Auth, Postgres con políticas RLS, y una importación diaria programada desde Adzuna mediante GitHub Actions.

**Estado de entrega:** Código completo listo para configurar y desplegar. No está publicado ni conectado a servicios reales todavía. Se necesitan cuentas propias y credenciales.

## 1. Crear el proyecto Supabase

1. Crea un proyecto en https://supabase.com/dashboard.
2. Abre **SQL Editor**. Copia `supabase.sql`, pero **antes de ejecutarlo cambia** los dos correos de ejemplo al final por el tuyo y el de Lucía (en minúsculas). Esos son los únicos correos autorizados a acceder a ofertas, notas y candidaturas.
3. En **Authentication > Providers > Email**, mantén activado el email y los enlaces de acceso (Magic Link). Crea los dos usuarios autorizados mediante **Authentication > Users > Add user > Send invitation** (uno por dirección). Si tu panel ofrece otros flujos equivalentes, comprueba que ambos usuarios existen antes de probar el enlace. Esta app usa `shouldCreateUser:false`: no autoriza altas de usuarios desde la pantalla pública.
4. En **Project Settings > API** (o **Connect** según versión del panel) copia el **Project URL** y la **publishable key** / **anon key**. Ambas pueden estar en el navegador. Edita `config.js` con sus valores. **No pongas aquí la service_role**.
5. En **Authentication > URL Configuration** configura la URL pública de la aplicación como **Site URL**, y añade exactamente esa URL (con barra final) en **Redirect URLs** para que los enlaces recibidos por correo vuelvan a la web.
6. Usa HTTPS y guarda una copia privada de las credenciales.

## 2. Publicar la web para instalarla en el móvil

1. Crea un repositorio en https://github.com/new (por ejemplo `radar-lucia`). Puedes hacerlo público porque la aplicación solo contiene código y claves públicas, pero **no subas el CV, números de teléfono, contraseñas ni claves privadas**.
2. Sube **el contenido** de esta carpeta (incluyendo `.github/workflows/`).
3. En GitHub, **Settings > Pages > Build and deployment > Deploy from a branch**, elige `main` y `/ (root)` y guarda. Se publicará en `https://USUARIO.github.io/radar-lucia/` (si ese es el nombre de tu repositorio).
4. Vuelve a Supabase y configura esa dirección como redirect para Magic Links.
5. En Android: abre la URL en Chrome > menú ⋮ > **Instalar aplicación** o **Añadir a pantalla de inicio**. En iPhone: Safari > Compartir > **Añadir a pantalla de inicio**. El navegador puede pedir volver a iniciar sesión.

**Nota:** Chrome/Android o Safari/iOS deben cargar una vez los recursos de la PWA. El inicio de sesión y las candidaturas compartidas necesitan conexión a Internet. La PWA cachea parte de su interfaz, pero no promete trabajar con las candidaturas sin conexión.

## 3. Obtener acceso a Adzuna

1. Entra en https://developer.adzuna.com/ y registra una aplicación API.
2. Obtén `app_id` y `app_key`. Revisa su cuota y condiciones de uso.
3. En el repositorio de GitHub: **Settings > Secrets and variables > Actions > New repository secret**; añade:
   - `ADZUNA_APP_ID`: identificador Adzuna.
   - `ADZUNA_APP_KEY`: clave privada Adzuna.
   - `SUPABASE_URL`: misma URL Supabase del paso 1.
   - `SUPABASE_SERVICE_ROLE_KEY`: clave Supabase **service_role** (o secret key con permisos administrativos adecuados), obtenida del panel Supabase. **Nunca la publiques en el código web o en config.js.**
4. Abre GitHub > **Actions > Buscar ofertas de empleo > Run workflow**. Comprueba el registro sin revelar las claves y mira las ofertas en la app.
5. Ya está incluido un workflow diario a las **08:17 Europe/Madrid**. GitHub puede retrasar ejecuciones programadas. Si la cuota gratuita no admite 28 consultas diarias, reduce las ciudades o palabras clave en `automation/fetch_jobs.py`.

## 4. Qué buscará

- 7 áreas: Madrid, Guadalajara, Toledo, Segovia, Ávila, Valladolid y Cuenca.
- 4 búsquedas por área: técnico calidad alimentaria, seguridad alimentaria, auditor alimentaria y APPCC.
- Ventana de anuncios de 14 días, por defecto hasta 25 resultados por búsqueda.
- Descarta resultados poco relacionados. Deduplica por identificador Adzuna; las candidaturas, notas y favoritos **no se borran ni se sobrescriben** en cada actualización.
- La inclusión de una ciudad o provincia es un filtro aproximado. **No mide el trayecto real en coche**: comprobad personalmente el municipio, la dirección exacta, la modalidad presencial y si está realmente a 2–3 horas de Madrid.
- Las notas y estados son compartidos entre los dos correos autorizados; no se sincronizan con LinkedIn, InfoJobs u otros sistemas de solicitud externos.

## 5. Seguridad y privacidad

- La web es pública a nivel de HTML, pero los datos de la tabla están protegidos por Supabase Auth + Row Level Security (RLS). Solo los dos correos registrados tienen acceso. Revisa que sustituiste los correos de ejemplo **antes de ejecutar SQL**.
- El secreto de servicio solo se utiliza en el runner de GitHub para importar ofertas. Jamás va al navegador.
- Es preferible crear un repositorio **privado** y alojar en un hosting estático compatible que permita esa modalidad si quieres proteger también el código fuente; comprueba las condiciones vigentes de GitHub Pages para repos privados. El código no lleva información personal del CV salvo reglas profesionales de puntuación.
- Las ofertas de terceros pueden expirar o variar y pueden enlazar a portales que requieren registro.
- La funcionalidad de actualización en tiempo real exige que la tabla se publique en Supabase Realtime. Si no funciona la suscripción, el botón **Actualizar** permite refrescar manualmente.

## 6. Comprobaciones

- Inicia sesión con el correo 1 y el correo 2 en navegadores diferentes. Si uno ve las ofertas y el otro no, revisa las direcciones de `allowed_emails` y los usuarios registrados.
- Marca una favorita desde un móvil y comprueba que se refleja en el otro (o pulsa Actualizar).
- Ejecuta el workflow manualmente y confirma nuevas ofertas.
- Comprueba que cada enlace abre el anuncio original. Verifica el tiempo en coche antes de solicitar.

## Errores frecuentes

- «No llegan enlaces»: usuario inexistente, supresión del correo, redirección no autorizada o proveedor Email desactivado.
- «Acceso sin ofertas»: RLS bloquea usuario no autorizado o no se han importado ofertas.
- «Workflow ERROR Missing secrets»: falta algún secret o se llamó con nombre distinto.
- «Adzuna 401/429»: credenciales incorrectas o cuota agotada. No hay reintentos ilimitados.
- «Página en blanco»: revisa `config.js`, el despliegue en la raíz y la consola del navegador.

## Archivos

- `index.html`, `style.css`, `app.js`: interfaz para móviles y ordenador.
- `manifest.webmanifest`, `sw.js`, `assets/`: instalación PWA.
- `config.js`: configuración *pública* de Supabase (editar antes de publicar).
- `supabase.sql`: tablas, usuarios autorizados y políticas de acceso.
- `automation/fetch_jobs.py`: importación diaria de ofertas Adzuna.
- `.github/workflows/daily-jobs.yml`: programación automática.

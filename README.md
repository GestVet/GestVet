# GestVet

Sistema web responsive para la gestión veterinaria: usuarios, mascotas, disponibilidad, citas, analítica e inteligencia asistida.

## Funcionalidades

Por módulo, lo que el sistema resuelve hoy:

**Cuentas y acceso** (`accounts`) — registro público de clientes (siempre como rol `client`, nunca elegido por quien se registra), alta de personal por administración, recuperación de contraseña por enlace de un solo uso, turno de guardia y respaldo de emergencias entre veterinarios. El DNI es obligatorio al registrarse. Cuando alguien llega a una emergencia sin cuenta, el personal puede darlo de alta en el momento con nombre, DNI y teléfono ("alta exprés"): la cuenta nace con un correo de relleno, inutilizable para entrar, y el personal completa el correo real después desde la ficha del cliente.

**Mascotas** (`pets`) — alta y baja por el dueño, con la especie elegida de una lista (más "Otro" a texto libre). La raza la edita el dueño cuando quiera; la fecha de nacimiento la confirma solo el veterinario, porque en una emergencia queda provisoria (la del día del alta exprés) hasta la primera consulta real. Los datos clínicos (peso, altura, esterilización, alergias) los carga el veterinario en consulta. El personal corrige el estado de una mascota si hubo un error de carga.

**Agenda** (`availability`) — publicación de tramos horarios por cada veterinario; una cita solo se agenda dentro de un tramo publicado.

**Citas** (`appointments`) — reserva, confirmación, finalización, cancelación (con motivo obligatorio) y marca de inasistencia, a mano o calculada sola al leer una cita que quedó vencida sin cerrar (no hace falta un proceso en segundo plano para eso). Apertura de emergencias sin elegir veterinario ni hora: el sistema asigna al que está de guardia, o a un veterinario normal habilitado como respaldo si no hay ninguno de guardia libre. El motivo de consulta muestra un aviso de "precio estimado, sujeto a variar según la atención".

**Historia clínica** (`medical_records`) — entradas por tipo (consulta, vacuna, cirugía, control, carta de consentimiento, otro), adjuntos por entrada, reporte en PDF de la historia completa de una mascota. La carta de consentimiento o el acuerdo de responsabilidad firmado en papel se escanea y se sube como un adjunto más: no hace falta ninguna pantalla aparte.

**Pagos** (`billing`) — registro manual de pagos (efectivo, Yape, transferencia, otro), anulación con motivo, cobro por QR con el monto de catálogo o un monto libre que fija el personal (con un margen acotado sobre citas normales, sin margen en emergencias, porque el costo real recién se sabe al terminar la atención), reporte de ingresos por medio de pago. La confirmación de un cobro por QR avisa al cliente por WhatsApp.

**Reseñas** (`reviews`) — calificación y comentario de un cliente sobre el veterinario que lo atendió, solo tras una cita completada, con un filtro básico de lenguaje ofensivo. El promedio queda visible al elegir veterinario para reservar.

**Reclamos** (`complaints`) — un cliente reclama sobre una cita propia, con el veterinario reclamado derivado de la cita (nunca elegido a mano), y puede adjuntar evidencia. La administración los revisa.

**Internaciones** (`hospitalizations`) — apertura desde una cita completada, con notas de seguimiento y alta médica; el cliente ve el historial de internación de su mascota en modo lectura desde su propia ficha.

**Panel de indicadores** (`insights`, solo administración) — cuatro señales calculadas con reglas fijas sobre datos que el sistema ya registra, sin ningún modelo de inteligencia artificial de por medio: recordatorios de cuidado vencido (vacuna o control), riesgo de inasistencia (un cliente con historial de citas sin cerrar y una cita próxima), pagos que se alejan del monto típico de su tipo de cita, y veterinarios con reseñas bajas o reclamos recientes.

**Notificaciones por WhatsApp** — confirmación de cita, recordatorio 24 horas antes (un proceso periódico dentro del propio backend, sin infraestructura nueva) y aviso de pago por QR confirmado. El adaptador de hoy, `ConsoleWhatsAppSender`, registra el mensaje en el log del servidor en vez de mandarlo de verdad, así que todo el flujo se puede probar completo sin ninguna cuenta externa. Falta conectar una cuenta real de WhatsApp Business API — ver la sección "WhatsApp Business API — pendiente" más abajo.

## Base tecnológica

### Backend

- Python 3.12 a 3.14
- FastAPI 0.141.1 con Uvicorn 0.52.4
- SQLAlchemy 2.0.52 en modo asíncrono, con Alembic 1.19.2
- Pydantic 2.13.5
- PyJWT 2.13.0 para los tokens de acceso
- PostgreSQL 15+ mediante `asyncpg`, con SQLite como respaldo local

### Frontend

- Node.js 24+ y pnpm 12
- React 19.3.0
- Vite 8.3.0
- TypeScript 6.0.3
- react-router 8.3.1 en modo librería
- TanStack Query 5.102.8 para el estado del servidor
- TanStack Table 9.2.4 para los listados
- React Hook Form 7.87.0 con Zod 4.6.1 para los formularios
- Zustand 5.0.15 para el estado de cliente
- react-big-calendar 1.20.0 para la agenda

Las versiones se verificaron el 10 de septiembre de 2026.

TypeScript queda fijado en la rama 6 a propósito. La versión 7 es el compilador reescrito en Go: verifica los mismos tipos, pero deja de exponer su API en JavaScript y rompe herramientas que dependen de ella, entre ellas `openapi-typescript`, que este proyecto usa para derivar los tipos del frontend desde el esquema OpenAPI del backend.

## Arquitectura

El backend sigue **arquitectura hexagonal estricta**, verificada por Import Linter en cada commit. Cada módulo de dominio tiene cuatro capas y la dependencia apunta siempre hacia adentro:

```text
backend/
├── alembic/                      # migraciones del esquema
├── scripts/                      # utilidades fuera de la aplicación
└── src/gestvet/
    ├── main.py                   # raíz de composición
    ├── core/                     # núcleo compartido
    │   ├── identity.py           # rol, principal y puerto de tokens
    │   ├── auth.py               # autenticación del borde HTTP
    │   ├── pagination.py         # forma de una página
    │   ├── activity.py           # bitácora: tipos de acción y puertos
    │   ├── config.py             # configuración por entorno
    │   ├── database.py           # motor y sesión
    │   ├── security.py           # cifrado de contraseñas
    │   └── tokens.py             # adaptador JWT
    └── modules/                  # módulos de dominio
        ├── accounts/             # cuentas, acceso y administración
        ├── pets/                 # mascotas
        ├── availability/         # agenda de los veterinarios
        ├── appointments/         # citas, motivos de consulta y emergencias
        ├── medical_records/      # historia clínica y adjuntos
        ├── billing/              # pagos, cobros por QR y reportes
        ├── reviews/              # reseñas de veterinarios
        ├── complaints/           # reclamos de clientes
        ├── hospitalizations/     # internaciones
        └── insights/             # panel de indicadores (BI con reglas fijas)
            ├── domain/           # Python puro: entidades y reglas
            ├── ports/            # interfaces que el negocio exige
            ├── use_cases/        # orquestación de las reglas
            └── adapters/         # única capa que toca tecnología
                ├── api/          # FastAPI
                └── persistence/  # SQLAlchemy
```

Los diez módulos comparten exactamente esa misma forma de cuatro capas; se muestra una sola vez para no repetirla diez veces.

Los módulos de dominio cuelgan de `modules/` y no de la raíz del paquete. Es lo que permite que los contratos los nombren con un comodín exacto y no lleven ni una excepción: el núcleo compartido y la raíz de composición quedan fuera por estar en otro sitio del árbol, no por estar exentos.

Quién es el usuario y qué rol tiene lo posee el núcleo, no `accounts`. Todos los módulos necesitan esa respuesta para autorizar, y si la tuviera un módulo de dominio el resto tendría que importarlo. El núcleo posee la autenticación; `accounts` posee la gestión de usuarios.

Cuando un módulo necesita un dato de otro, declara la pregunta como un puerto de lectura y un adaptador la responde leyendo la tabla ajena. Las citas preguntan si la mascota es del cliente y si el veterinario publicó esa hora. Se lee, nunca se escribe.

La bitácora de movimientos vive en el núcleo por la misma razón que la identidad: la escriben todos los módulos. El núcleo guarda quién, qué y cuándo; el nombre y el rol los pone `accounts` al leerla, porque son suyos.

`domain`, `ports` y `use_cases` tienen prohibido importar FastAPI, SQLAlchemy o cualquier otro detalle de infraestructura. Eso no es una convención: es un contrato que falla el commit si se rompe.

Un adaptador vive en el núcleo compartido solo si no habla ningún tipo de negocio. El cifrado de contraseñas cumple esa condición, porque recibe y devuelve texto. El servicio de tokens no, porque construye los tipos que declara su puerto, así que vive en `accounts/adapters/security`.

El frontend usa **arquitectura por características**, con límites verificados por `eslint-plugin-boundaries`:

```text
frontend/src/
├── api/          contrato generado desde OpenAPI y funciones de consulta
├── components/   piezas de interfaz compartidas, incluido el registro de iconos
├── features/     un módulo por pantalla; no pueden importarse entre sí
├── hooks/        ayudas transversales
├── router/       rutas y guardas
├── services/     cliente HTTP centralizado
└── store/        estado de cliente
```

`main.tsx` es la raíz de composición y está declarada como tal, con una política propia que le permite alcanzar todas las capas. No está exenta: un archivo exento no tiene reglas, y este las tiene, solo que amplias. El armazón de la interfaz vive en `components` porque es lo que es, un componente compartido.

Ningún archivo puede ser un *barrel file*, es decir uno que solo reexporta. Enturbian los límites, esconden dependencias circulares y hacen que un import arrastre módulos que nadie pidió.

## Requisitos

- Python 3.12 a 3.14
- Node.js 24+
- `uv`
- `pnpm` 12
- Docker Desktop

## Puesta en marcha

Desde la raíz del repositorio:

```powershell
Copy-Item backend/.env.example backend/.env
pnpm install
uv sync --directory backend --group dev
docker compose up -d db
pnpm migrate
```

`pnpm install` instala el monorepositorio entero, raíz y frontend, y activa los hooks de Git de Husky. Todo el repositorio es un único espacio de trabajo de pnpm con un solo archivo de bloqueo.

Antes de arrancar hay que definir `JWT_SECRET_KEY` en `backend/.env`. Necesita 32 bytes como mínimo, y con `DEBUG=false` la aplicación se niega a arrancar si conserva el valor de ejemplo. Para generar uno:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

En una terminal, iniciar el API:

```powershell
uv run --directory backend uvicorn gestvet.main:app --app-dir src --reload
```

En otra terminal, iniciar el frontend:

```powershell
pnpm --filter gestvet-frontend dev
```

URLs locales:

- Frontend: <http://localhost:5173>
- API: <http://127.0.0.1:8000/api/v1/health>
- Documentación interactiva: <http://127.0.0.1:8000/api/v1/docs>
- Esquema OpenAPI: <http://127.0.0.1:8000/api/v1/openapi.json>

Todo cuelga de `/api/v1`, documentación y esquema incluidos, para que el proxy del frontend, que solo reenvía `/api`, los alcance sin reglas aparte.

## Base de datos

El esquema lo crean las migraciones, también en desarrollo:

```powershell
pnpm migrate                                              # aplicar hasta la última
uv run --directory backend alembic downgrade -1           # deshacer una
uv run --directory backend alembic revision --autogenerate -m "descripcion"
```

La aplicación no crea tablas al arrancar. Hacerlo dejaba que la base local se apartara del historial de migraciones sin que nadie se enterara hasta el despliegue. Una prueba aplica las migraciones sobre una base vacía y compara el resultado contra el modelo: si divergen, falla y dice qué migración falta.

## Contrato con el frontend

Los tipos del frontend se derivan del esquema OpenAPI del backend. No hace falta el servidor en marcha:

```powershell
pnpm generate:api
```

Eso vuelca el esquema con `backend/scripts/export_openapi.py` y reescribe `frontend/src/api/schema.d.ts`. Un cambio de campo en el backend rompe el build del frontend en lugar de fallar en ejecución. La integración continua regenera el archivo y falla si el commit lo dejó desactualizado.

## Validaciones

Todo de una vez, desde la raíz:

```powershell
pnpm verify
```

O por separado:

```powershell
pnpm lint:backend     # Ruff
pnpm arch:backend     # contratos de arquitectura hexagonal
pnpm test:backend     # pytest
pnpm lint:frontend    # ESLint estricto
pnpm build:frontend   # verificación de tipos y compilación
```

Las mismas comprobaciones corren en GitHub Actions ante cada push y cada pull request contra `main` y `develop`, el backend sobre las tres versiones de Python admitidas. El hook de Git es una comodidad y se puede saltar con `--no-verify`; la integración continua no.

En las pruebas, un aviso de Python es un fallo. Es la forma barata de enterarse de una deprecación cuando todavía queda una versión de margen para atenderla.

## Reglas que el linter aplica solo

En el backend, Import Linter verifica cuatro contratos: las capas hexagonales dentro de cada módulo, que el dominio no conozca la tecnología, que los módulos de dominio no se importen entre sí, y que el núcleo compartido no dependa del dominio.

Los cuatro se escriben con comodines sobre `gestvet.modules.*` en lugar de nombrar los módulos uno por uno. La diferencia importa: un módulo nuevo queda cubierto el día que se crea, sin que nadie tenga que acordarse de editar `pyproject.toml`. La regla de independencia usa un contrato `independence`, que es simétrico, y no uno `forbidden`, que solo mira en una dirección y dejaría que el módulo nuevo importara a los que ya estaban.

Ninguno de los cuatro lleva excepciones, y tampoco hay un solo `noqa` en el backend. Una excepción escrita al lado de una regla la vacía en silencio: quien lee el contrato cree que se cumple. Cuando hizo falta una, se cambió la estructura hasta que dejó de hacer falta.

La lista de tecnología prohibida en el dominio incluye toda dependencia de tercero del proyecto, no solo el ORM y el framework web. El dominio es Python puro: tampoco puede conocer Pydantic, ni la librería de cifrado, ni la de tokens.

En el frontend, ESLint aplica:

| Regla | Principio |
| --- | --- |
| Una característica no importa otra característica | Bajo acoplamiento |
| Ninguna capa importa un archivo fuera de la arquitectura | Bajo acoplamiento |
| Ningún archivo reexporta lo de otro | Límites explícitos |
| Comentarios sin código muerto ni tareas pendientes | Higiene |
| Un solo componente de React por archivo | Responsabilidad única |
| Carpetas en kebab-case, componentes en PascalCase | Nombrado consistente |
| Complejidad cognitiva, profundidad y largo acotados | KISS |
| Funciones idénticas y literales repetidos prohibidos | DRY |
| Tipado estricto con verificación de tipos | Corrección |

El análisis de límites abarca todo `src`, no la lista de capas conocidas. Enumerarlas dejaba fuera cualquier carpeta nueva: un `src/utils/` recién creado no era una violación, era invisible, y todas las capas podían importarlo. La raíz de composición sigue exenta, que es lo único que debe estarlo.

## Comentarios

Un comentario se gana su lugar solo si dice algo que el código no puede decir. El código ya dice **qué** hace; el comentario está para lo que no cabe en un nombre.

Se comenta cuando aplica una de estas tres:

- **Por qué está así.** La razón de una decisión que de otro modo parece arbitraria o equivocada: una restricción de afuera, un rodeo, un intercambio deliberado. *"SQLite no almacena la zona, así que una fecha guardada con UTC vuelve ingenua."*
- **Qué se rompe si lo tocás.** Una invariante que no se ve desde donde está el código. *"Sin la compilación de este resolutor, las reglas de límites quedan inertes y no avisan."*
- **Un contrato que el nombre no alcanza a expresar.** Sobre todo en los puertos, donde la firma no dice para qué existe la operación. *"Hash válido que ninguna contraseña reproduce: al autenticar un correo que no existe hay que gastar el mismo tiempo que con uno real."*

No se comenta:

- Repetir el nombre del archivo, de la clase o de la función. Un `"""Modelo de persistencia."""` encima de `models.py` no agrega nada y envejece cuando el archivo cambia de rol.
- Repetir la firma. Los tipos ya están escritos.
- Escribir una regla del proyecto en cada archivo que la cumple. Una regla se explica una vez, acá, y los archivos la siguen en silencio.
- Rotular secciones dentro de un archivo de código. Si un archivo necesita separadores para navegarse, lo que quiere es partirse en dos. En una hoja de estilo o en un archivo de configuración sí ayudan, porque son listas largas y planas sin estructura propia.
- Dejar código comentado, ni tareas pendientes. Lo primero lo guarda el control de versiones; lo segundo, el gestor de incidencias.

En el backend un docstring es opcional a propósito. Obligar a documentar cada módulo y cada función es justo lo que produce la línea que repite el nombre del archivo.

### Qué verifica la herramienta y qué no

Esta distinción importa, porque es fácil creer que un linter resuelve el problema. No lo resuelve: **ninguna herramienta puede decidir si un comentario aporta algo.** Eso queda en la regla escrita y en la revisión. Lo que sí se verifica es la higiene:

| Qué se rechaza | Con qué |
| --- | --- |
| Código comentado | `ERA001` de Ruff |
| Un `TODO` o un `FIXME` en el árbol | `FIX` de Ruff, `no-warning-comments` y `sonarjs` en ESLint |
| Un docstring mal formado, cuando existe | Las reglas de forma de pydocstyle, `D200` en adelante |
| Un comentario al final de una línea de código | `no-inline-comments` |
| Barras sin espacio, bloques de estilo mezclado | `spaced-comment`, `multiline-comment-style` |
| Desactivar una regla sin decir por qué | `@eslint-community/eslint-comments` |

Las reglas de pydocstyle que **exigen** la presencia de un docstring, de `D100` a `D107`, quedan fuera a propósito. Son las que empujan a escribir relleno.

Las directivas `eslint-disable` no están prohibidas del todo. Prohibirlas empuja la excepción al archivo de configuración, donde vale para el proyecto entero y es mucho peor que una línea acotada. Lo que se exige es que sean estrechas y que digan por qué, que es la misma vara con la que el proyecto trata cualquier otra excepción.

## Iconos

Todos los iconos salen de un registro único, `src/components/icons.ts`. Un icono es un dato, no un componente: el trazo vive en ese archivo y lo dibuja `Icon.tsx`, que es el único componente que emite un `<svg>` en todo el frontend.

```tsx
<Icon name="mascota" size={20} />
```

Cambiar el icono de citas por otro es editar una línea del registro y verlo en cada pantalla. El nombre está tipado contra el propio registro, así que pedir uno que no existe no compila. Tres nombres comparten trazo a propósito, porque lo que los separa es el significado: el día que el perfil propio necesite un dibujo distinto del listado de clientes, se cambia una sola línea.

El menú de la aplicación sigue la misma idea. `src/features/shell/navigation.ts` declara cada entrada con su ruta, su etiqueta, su icono y los roles que la ven, así que agregar una pantalla es agregar una línea.

## Interfaz

La identidad visual viene del proyecto original: el azul institucional, el verde de las acciones afirmativas y las tarjetas blancas sobre gris. Allá estaban repetidos a mano en veintiséis hojas de estilo; acá viven una sola vez como variables CSS.

| Pantalla | Quién |
| --- | --- |
| Portada, acceso, registro y recuperación de contraseña | cualquiera |
| Panel y perfil | cuenta autenticada |
| Citas | cuenta autenticada, recortado por rol |
| Mis mascotas y reservar | cliente |
| Mi agenda | veterinarios |
| Clientes | personal de la clínica |
| Emergencia (cliente nuevo) | personal de la clínica |
| Personal | administración |
| Pagos | administración |
| Reclamos | administración |
| Indicadores | administración |
| Movimientos | administración |

Las guardas de ruta son una comodidad de la interfaz, no una medida de seguridad: quien llegue igual a una pantalla se encuentra con un 401 o un 403 del servidor. La autorización de verdad vive en el backend y está cubierta por pruebas.

## Movimientos

Cada acción que completa una cuenta deja un asiento: quién, qué, cuándo y un detalle corto. La administración los consulta en `/movimientos`, con filtro por rol y por tipo de acción.

Quien escribe el asiento es el caso de uso, no el endpoint. Registrar forma parte de la operación, y va en su misma transacción: si la operación se deshace, el asiento se va con ella.

Dos diferencias con el sistema original:

El tipo de acción es un código estable y no una frase armada a mano. El original guardaba textos como *"Reservó cita de tipo Consulta general"*, y cada variante de la redacción era un valor distinto, así que no se podía filtrar ni contar. Acá la frase legible se arma al mostrarla y cambiarla no rompe el historial.

Las acciones de la administración también se registran y se muestran. El original las escondía con un `id_rol != 1` fijo en la consulta, y una bitácora que oculta al actor más poderoso no sirve para auditar.

Lo que la bitácora no guarda son los intentos fallidos. Un acceso con contraseña equivocada no deja rastro, porque el asiento se escribe recién cuando la operación sale bien.

## Acceso y autorización

El registro es público y siempre crea un cliente. El campo `role` no existe en el cuerpo de la petición, así que ningún visitante puede pedir un rol privilegiado: el servidor lo fija.

`POST /api/v1/auth/login` intercambia credenciales por un token de portador. Un acceso fallido responde siempre lo mismo, exista o no la cuenta, y la contraseña se verifica incluso cuando el correo no existe, para que la latencia de la respuesta no delate qué direcciones están registradas.

El rol y el estado de la cuenta se releen de la base en cada petición y no se toman del token, así que una cuenta degradada o desactivada pierde el acceso sin esperar a que el token venza.

El padrón de clientes es dato personal: solo lo ve el personal de la clínica.

| Endpoint | Quién |
| --- | --- |
| `POST /api/v1/auth/register` | cualquiera |
| `POST /api/v1/auth/login` | cualquiera |
| `GET /api/v1/auth/me` | cuenta autenticada |
| `GET /api/v1/clients` | administración y veterinarios |
| `GET /api/v1/activity` | administración |

## WhatsApp Business API — pendiente

El código ya está listo del lado de GestVet. `gestvet.core.whatsapp.WhatsAppSender` es el puerto (un `Protocol`, sin saber nada de negocio) y está conectado en tres puntos: confirmar una cita, confirmar un pago por QR, y un recordatorio 24 horas antes que corre en un `asyncio.Task` dentro del propio proceso del backend, sin agregar ninguna dependencia nueva ni un servicio aparte. El adaptador de hoy, `ConsoleWhatsAppSender`, registra cada mensaje en el log en vez de mandarlo, así que todo el flujo se prueba completo en desarrollo.

Lo que falta depende de la clínica, no del código:

1. **Elegir el camino**: directo con Meta (Cloud API — gratis salvo el costo por conversación, pero con una verificación de negocio que puede demorar) o vía un intermediario (Twilio, 360dialog, etc. — más rápido de activar, con un costo mensual fijo además del costo por mensaje).
2. **Verificar el negocio** ante Meta con el RUC y los documentos de la clínica.
3. **Dar de alta las plantillas de mensaje** (confirmación de cita, recordatorio, pago confirmado) para que Meta las apruebe: un mensaje fuera de plantilla no se puede mandar fuera de una conversación que el cliente ya inició.
4. **Reemplazar el adaptador**: una clase nueva que satisfaga `WhatsAppSender` llamando a la API real, y una línea a cambiar en `get_whatsapp_sender()` de `appointments/adapters/api/dependencies.py` y de `billing/adapters/api/dependencies.py`. Ningún caso de uso cambia; el puerto es el mismo.

Hasta que exista esa cuenta, todo mensaje queda solo en el log del servidor, visible para quien opere el despliegue.

## Convenciones iniciales

- API versionada desde `/api/v1/`.
- Fechas en UTC y conversiones únicamente en la interfaz.
- Listados paginados y filtrables desde el backend.
- Autorización por rol y propiedad del recurso, aplicada acotando el conjunto de datos antes de tocar un objeto por identificador.
- El rol nunca llega desde el cliente: el servidor lo fija.
- Las consultas BI no deben modificar el modelo transaccional.
- Las funciones de IA nunca ejecutan SQL libre ni reciben datos fuera de los permisos del usuario.
- Los secretos solo viven en archivos `.env` locales o en el gestor de secretos del despliegue.
- Los hooks de Git los gestiona Husky desde `.husky/`. El hook `commit-msg` rechaza líneas `Co-authored-by`, y `pre-commit` corre los linters y los contratos de arquitectura.

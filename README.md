# GestVet

Sistema web responsive para la gestión veterinaria: usuarios, mascotas, disponibilidad, citas, analítica e inteligencia asistida.

## Funcionalidades

Por módulo, lo que el sistema resuelve hoy:

**Cuentas y acceso** (`accounts`) — registro público de clientes (siempre como rol `client`, nunca elegido por quien se registra), alta de personal por administración, recuperación de contraseña por enlace de un solo uso, y roles con permisos editables por la administración. El DNI es obligatorio al registrarse. Cuando alguien llega a una emergencia sin cuenta, el personal puede darlo de alta en el momento con nombre, DNI y teléfono ("alta exprés"): la cuenta nace con un correo de relleno, inutilizable para entrar, y el personal completa el correo real después desde la ficha del cliente.

**Mascotas** (`pets`) — alta y baja por el dueño, con la especie y la raza elegidas de un catálogo que la administración amplía cuando llega un animal que no está. Especie, raza, fecha de nacimiento, sexo, color, microchip y temperamento los edita el dueño desde su ficha; el veterinario también puede corregir la fecha de nacimiento, que en una emergencia queda provisoria (la del día del alta exprés) hasta la primera consulta real. Los datos clínicos (peso, altura, esterilización, alergias) los carga el veterinario en consulta. El personal corrige el estado de una mascota si hubo un error de carga.

**Agenda** (`availability`) — la clínica asigna los turnos de cada veterinario, y la guardia es un tipo de turno más; una cita solo se agenda dentro de un turno asignado.

**Citas** (`appointments`) — reserva, confirmación, finalización, cancelación (con motivo obligatorio) y marca de inasistencia, a mano o calculada sola al leer una cita que quedó vencida sin cerrar (no hace falta un proceso en segundo plano para eso). Apertura de emergencias sin elegir veterinario ni hora: el sistema asigna al veterinario de guardia menos cargado o, si no hay ninguno libre, a uno en turno de atención con el resto del día libre. El motivo de consulta muestra un aviso de "precio estimado, sujeto a variar según la atención".

**Historia clínica** (`medical_records`) — entradas por tipo (consulta, vacuna, cirugía, control, carta de consentimiento, otro), adjuntos por entrada, reporte en PDF de la historia completa de una mascota. La carta de consentimiento o el acuerdo de responsabilidad firmado en papel se escanea y se sube como un adjunto más: no hace falta ninguna pantalla aparte.

**Pagos** (`billing`) — registro manual de pagos (efectivo, Yape, transferencia, otro), anulación con motivo, cobro por QR con el monto de catálogo o un monto libre que fija el personal (con un margen acotado sobre citas normales, sin margen en emergencias, porque el costo real recién se sabe al terminar la atención), reporte de ingresos por medio de pago. La confirmación de un cobro por QR avisa al cliente por WhatsApp.

**Reseñas** (`reviews`) — calificación y comentario de un cliente sobre el veterinario que lo atendió, solo tras una cita completada, con un filtro básico de lenguaje ofensivo. El promedio queda visible al elegir veterinario para reservar.

**Reclamos** (`complaints`) — un cliente reclama sobre una cita propia, con el veterinario reclamado derivado de la cita (nunca elegido a mano), y puede adjuntar evidencia. La administración los revisa.

**Internaciones** (`hospitalizations`) — apertura desde una cita completada, con notas de seguimiento y alta médica; el cliente ve el historial de internación de su mascota en modo lectura desde su propia ficha.

**Panel de indicadores** (`insights`, solo administración) — cuatro señales calculadas con reglas fijas sobre datos que el sistema ya registra, sin ningún modelo de inteligencia artificial de por medio: recordatorios de cuidado vencido (vacuna o control), riesgo de inasistencia (un cliente con historial de citas sin cerrar y una cita próxima), pagos que se alejan del monto típico de su tipo de cita, y veterinarios con reseñas bajas o reclamos recientes.

**Notificaciones por WhatsApp** — confirmación de cita, recordatorio 24 horas antes, aviso una semana antes de la próxima dosis de una vacuna (los dos recordatorios son un proceso periódico dentro del propio backend, sin infraestructura nueva) y aviso de pago por QR confirmado. El adaptador de hoy, `ConsoleWhatsAppSender`, registra el mensaje en el log del servidor en vez de mandarlo de verdad, así que todo el flujo se puede probar completo sin ninguna cuenta externa. Falta conectar una cuenta real de WhatsApp Business API — ver la sección "WhatsApp Business API — pendiente" más abajo.

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
- shadcn/ui 4.21 sobre Radix, con Tailwind CSS 4.3
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
│   └── ui/       componentes de shadcn/ui, generados por su CLI
├── features/     un módulo por pantalla; no pueden importarse entre sí
├── hooks/        ayudas transversales
├── router/       rutas y guardas
├── services/     cliente HTTP centralizado
└── store/        estado de cliente
```

`main.tsx` es la raíz de composición y está declarada como tal, con una política propia que le permite alcanzar todas las capas. No está exenta: un archivo exento no tiene reglas, y este las tiene, solo que amplias. El armazón de la interfaz vive en `components` porque es lo que es, un componente compartido.

Ningún archivo puede ser un *barrel file*, es decir uno que solo reexporta. Enturbian los límites, esconden dependencias circulares y hacen que un import arrastre módulos que nadie pidió.

## shadcn/ui y Tailwind

La interfaz se construye con shadcn/ui sobre Tailwind CSS, y cualquier tabla usa TanStack Table. Para agregar un componente:

```powershell
Set-Location frontend
pnpm dlx shadcn@latest add dialog
```

Los componentes caen en `src/components/ui`. Es código que genera y actualiza el CLI de shadcn, así que se respeta su forma:

- **Nombres en kebab-case.** La carpeta tiene su propia convención de nombres en vez de una excepción, porque renombrar los archivos rompería cada `shadcn add`.
- **Dos reglas no aplican ahí.** Cada archivo agrupa una familia de componentes y algunos exportan sus variantes. El resto del lint, tipado estricto incluido, se aplica igual.
- **Lucide y Radix solo se importan dentro de `ui`.** El resto de la aplicación usa el registro único de iconos y los componentes ya tematizados; el lint rechaza la importación directa.

El `cn` que usan los componentes viene del paquete `cn`, que es lo que emite hoy el registro de shadcn. No hay `src/lib`: el `.gitignore` de la raíz ignora cualquier carpeta `lib/`, y un archivo ahí nunca llegaría al repositorio.

### Tablas

Todos los listados usan `components/DataTable.tsx`, que monta TanStack Table 9 sobre la tabla de shadcn y resuelve lo común: carga, vacío, desplazamiento horizontal en el celular y filas que se despliegan. Cada pantalla declara sus columnas con una forma propia (`id`, `header`, `cell`) y no con los genéricos de TanStack, que cambiaron enteros de la 8 a la 9.

En el celular la tabla se desplaza en vez de apilarse: WCAG exime a las tablas de datos del reflujo, y apilarla le quita las cabeceras al lector de pantalla.

### Tema

Los tokens de shadcn en `src/index.css` llevan la paleta de GestVet: el azul institucional `#004b8d` es `primary`, el verde de las acciones afirmativas es `success` (con su variante de botón) y el fondo gris azulado es `background`. Es la misma identidad que tenía la interfaz original.

Donde un color original no alcanza el contraste de WCAG 2.2 AA se oscurece lo justo, y el archivo anota por qué: el verde con texto blanco, el gris de texto secundario y el borde de los campos. No hay tema oscuro.

### Sin CSS escrito a mano

Toda la interfaz está en componentes de shadcn y utilidades de Tailwind. No queda `style.css` ni capa `legacy`. Las piezas repetidas viven en `src/components`: `PageHeader`, `SectionCard`, `EmptyState`, `DataTable`, `ConfirmDialog`, `StatusBadge` y los campos `TextField`, `SelectField` y `TextareaField`, que enlazan su ayuda y su error con `aria-describedby`.

Las confirmaciones y los motivos (cancelar una cita, anular un pago, corregir el estado de una mascota) se piden en un diálogo y no con `window.confirm` o `window.prompt`, que no toman el tema y no se leen bien con lector de pantalla.

Con sesión iniciada, el menú va en una barra lateral desde 1024 px y detrás de un botón en pantallas más angostas. Las entradas salen de `features/shell/navigation.ts`.

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
uv run --directory backend uvicorn gestvet.main:app --app-dir src --reload --reload-dir src --timeout-graceful-shutdown 3
```

`--reload-dir src` evita que la instalación de un paquete en `.venv` dispare una recarga. `--timeout-graceful-shutdown 3` hace falta por el canal de tiempo real: uvicorn espera a que terminen todas las respuestas antes de recargar, y una conexión de avisos no termina nunca; sin el límite, un navegador abierto deja la recarga colgada. Al cortarse, el navegador se reconecta solo.

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

## Logs

El backend registra con [structlog](https://www.structlog.org/) y el frontend con [Pino](https://getpino.io/), en su versión para navegador.

En el backend todo sale con el mismo formato, también lo que escriben uvicorn o SQLAlchemy. En desarrollo va a la consola con color; en un despliegue conviene una línea JSON por evento:

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Nivel mínimo: `DEBUG`, `INFO`, `WARNING` o `ERROR` |
| `LOG_JSON` | `false` | `true` escribe JSON en vez de texto con color |

Cada petición deja un evento `request.completed` con método, ruta, estado y duración. Una respuesta 4xx sale como aviso y una 5xx como error, con la traza. Los eventos de acceso quedan como `auth.*`: altas, ingresos, ingresos fallidos y recuperación de contraseña. Las claves `password`, `token` y `authorization` se escriben siempre como `[oculto]`, y los correos de un ingreso fallido van enmascarados (`j***@example.com`).

Cada petición lleva un identificador en la cabecera `X-Request-ID`. Lo genera el frontend y el backend lo devuelve en la respuesta, así que un error de la consola del navegador y su línea en el servidor se encuentran buscando el mismo valor.

En el frontend el nivel se fija con `VITE_LOG_LEVEL`; sin definirlo es `debug` en desarrollo y `warn` en producción. Se registran las peticiones que fallan (`http.request_failed`, `http.request_rejected`), los errores que nadie capturó y los de React, con su pila de componentes. Ningún evento lleva cuerpos de petición ni tokens.

## Tiempo real

Las pantallas abiertas se actualizan solas cuando cambia una cita: el veterinario ve la reserva nueva o la emergencia asignada, y el cliente la confirmación o la cancelación, sin recargar.

Funciona con Server-Sent Events en `GET /api/v1/events`. Es un canal de un solo sentido: el servidor avisa y el navegador escucha; las acciones siguen yendo por la API normal. El aviso no trae datos, solo el tema y el identificador (`appointments`, cita 42). El frontend marca como desactualizadas las consultas de ese tema y React Query vuelve a pedir las que están en pantalla, así que los permisos por rol siguen decidiéndose en un solo lugar.

- Un aviso sale recién cuando la transacción se confirma. Si se deshace, no sale.
- Cada conexión recibe solo los avisos de su cuenta: una cita avisa a su cliente, a su veterinario y a la administración.
- Con PostgreSQL los avisos se reparten entre procesos con `LISTEN/NOTIFY`, así que no hace falta Redis ni RabbitMQ. Con SQLite, o si no logra escuchar, se reparten dentro del proceso.
- El navegador lee el canal con `fetch` para poder mandar el token en la cabecera, y reconecta solo con espera creciente. Al reconectar vuelve a pedir lo que pudo cambiar mientras no hubo conexión.
- El sondeo de avisos quedó cada 60 segundos, como respaldo si el canal se corta.

Detrás de Nginx, esa ruta necesita `proxy_buffering off;` y un `proxy_read_timeout` largo; el servidor manda un ping cada 15 segundos para que ningún proxy la cierre por inactividad. Al desplegar o reiniciar, el proceso debe arrancar con un `--timeout-graceful-shutdown` corto, por la misma razón que en desarrollo.

## Base de datos

El esquema lo crean las migraciones, también en desarrollo:

```powershell
pnpm migrate                                              # aplicar hasta la última
uv run --directory backend alembic downgrade -1           # deshacer una
uv run --directory backend alembic revision --autogenerate -m "descripcion"
```

Para revisar las pantallas privadas hay cuentas de prueba, una por rol, que siembra un script. Solo corre contra una base local y es idempotente:

```powershell
pnpm seed
```

| Rol | Correo |
|---|---|
| Administrador | `admin.demo@example.com` |
| Cliente, con una mascota | `cliente.demo@example.com` |
| Veterinario | `veterinario.demo@example.com` |
| Veterinario de emergencia | `guardia.demo@example.com` |

Todas usan la contraseña `gestvet-demo-2026`. El dominio `example.com` está reservado, así que ninguna cuenta puede ser de una persona real.

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
| `GET /api/v1/auth/me` | cuenta autenticada; trae su rol y sus permisos |
| `GET /api/v1/clients` | permiso `clients.read` |
| `GET /api/v1/activity` | permiso `activity.read` |
| `/api/v1/access/*` | permiso `roles.manage` |

### Especies y razas

La especie y la raza de una mascota se eligen de un catálogo, no se escriben. Con texto libre, "perro", "Perro" y "can" eran tres especies distintas para cualquier búsqueda o indicador.

- **Contenido.** Vive en la base, en `pet_species` y `pet_breeds`. La migración 0020 siembra 21 especies, de las mascotas comunes a los animales de granja, con sus razas habituales en el Perú: el perro sin pelo del Perú, el cuy andino, el caballo peruano de paso, la alpaca y la llama. Toda especie tiene "Sin especificar", que es lo que deja el alta exprés de una emergencia; esa raza no se renombra ni se desactiva.
- **Administración.** La pantalla *Especies y razas* (permiso `pets.manage_catalog`, de la administración por defecto) agrega especies y razas, corrige nombres y desactiva lo que ya no se usa. Nada se borra: una raza desactivada sale de los formularios, pero las mascotas que ya la tienen la conservan. Corregir un nombre lo corrige también en esas fichas. Cada cambio llega al instante a los formularios abiertos por el tema `pet-catalog` del canal en tiempo real.
- **Formato único.** Todo nombre se guarda con mayúscula solo al inicio, sin espacios de más: "PASTOR ALEMÁN" y "pastor alemán" quedan "Pastor alemán". Un nombre propio conserva su mayúscula si quien escribe deja otra palabra en minúscula, como en "perro sin pelo del Perú". Dos nombres que solo difieren en tildes o mayúsculas son el mismo y no entran dos veces. La regla vive en `modules/pets/domain/catalog.py`; `services/catalogName.ts` la repite solo para mostrar mientras se escribe cómo va a quedar.
- **Validación.** El servidor la aplica al registrar y al editar la ficha, solo con lo que se ofrece hoy. Al editar, se valida la especie y la raza únicamente si cambian. El frontend pide la lista a `GET /api/v1/pets/catalog` y la raza depende de la especie elegida.
- **Ficha del dueño.** Además del sexo, el color, el microchip y el temperamento, el dueño corrige la especie, la raza y la fecha de nacimiento. Así completa una mascota dada de alta en una emergencia. Una mascota cargada antes del catálogo conserva su texto hasta que alguien lo cambie.
- **Otras validaciones.**
  - La fecha de nacimiento no puede estar en el futuro ni ser de hace más de 60 años.
  - El microchip tiene de 9 a 15 dígitos.
  - El peso va hasta 120 kg y la altura hasta 200 cm.
  - Los textos respetan los topes del servidor, y los motivos y descripciones piden al menos 5 caracteres.

Las reglas compartidas del frontend están en dos archivos:

- `components/formRules.ts`: textos, números y datos de la mascota.
- `services/fieldRules.ts`: nombres, DNI, teléfono, correo y contraseña.

### Turnos y guardias

Los turnos los asigna la clínica, no el veterinario. Así trabajan las veterinarias de Trujillo: atención de día y una guardia de noche que cubre las emergencias.

- **Dos tipos de turno.** En uno de *atención* el veterinario recibe citas; empieza y termina el mismo día y dura hasta 12 horas. En una *guardia* cubre las emergencias, puede cruzar la medianoche y dura hasta 24 horas. La guardia no se ofrece para reservar. Ya no existe un rol "veterinario de guardia": cualquier veterinario puede tener guardias.
- **Asignación.** La administración, con el permiso `schedule.manage`, asigna turnos sueltos o aplica un horario semanal de 1 a 12 semanas. El horario se aplica entero o no se aplica: si un día choca con otro turno, no se crea ninguno.
- **Validaciones.** Hay tres, en el servidor y en el formulario:
  - un turno no se asigna en un día que ya pasó ni a más de un año;
  - dos turnos del mismo veterinario no se cruzan;
  - un turno con citas reservadas no se puede quitar.
- **Emergencias.** Se asignan al veterinario de guardia menos cargado. Si todos ya atienden una o nadie está de guardia a esa hora, cubre un veterinario en turno de atención que tenga libre el resto del día.
- **Pedidos de cambio.** El veterinario (`schedule.read_own`, `schedule.request_change`) ve sus turnos por semana y pide cambios. La administración acepta o rechaza con una respuesta. Aceptar no mueve el turno: se reasigna a mano, porque un cambio suele necesitar a otro veterinario que lo cubra.
- **Tiempo real.** Cada cambio avisa por el tema `schedule` al veterinario afectado y a la administración.
- **Datos de prueba.** `scripts/seed_dev.py` asigna a `veterinario.demo` atención de lunes a sábado de 9 a 18, y a `guardia.demo` guardia todas las noches de 20 a 8, las próximas cuatro semanas.

### Roles y permisos

Cada endpoint exige un **permiso**, no un rol: `Depends(require_permission(Permission.X))`. Hay dos ideas separadas:

- **Tipo de cuenta** (`users.role`: cliente, veterinario, administración). No cambia y decide qué datos ve la cuenta. Por ejemplo, un cliente solo ve sus propias citas.
- **Rol de acceso** (`access_roles`). Es un conjunto de permisos que la administración edita desde *Roles y permisos*.

Detalles:

- **Catálogo.** Vive en `core/permissions.py`. Cada permiso declara qué tipos de cuenta pueden tenerlo: a un cliente no se le puede dar `appointments.attend`. Agregar un permiso es sumar una línea al catálogo y usarlo en el endpoint. Si además cambian los permisos por defecto, hace falta una migración que siembre el cambio. Una prueba compara la semilla con el código.
- **Roles por defecto.** Cada tipo de cuenta tiene un rol de sistema, que la migración 0017 siembra con los permisos de antes. Una cuenta sin rol asignado usa el de su tipo. Estos roles se editan pero no se renombran ni se borran.
- **Roles propios.** La administración los crea para un tipo de cuenta y los asigna desde *Personal*. Un rol asignado a alguien no se puede borrar.
- **Protecciones.** El rol de administración por defecto no pierde `roles.manage`. Nadie se quita ese permiso de su propio rol y nadie cambia su propio rol. Así la clínica no se queda sin quien administre.
- **Permisos por petición.** Se leen de la base en cada petición con una sola consulta. Un cambio rige en la siguiente petición, sin esperar a que venza el token.
- **Interfaz.** La sesión guarda los permisos. El menú (`navigation.ts`), las rutas (`RequireSession`) y cada botón (`useCan('...')`) preguntan por permisos, nunca por roles. Cuando un rol cambia, el servidor avisa por el tema `permissions` del canal en tiempo real. La interfaz vuelve a pedir `/auth/me` y oculta lo que ya no corresponde sin recargar. Ocultar es comodidad: el servidor igual responde 403.

## Verificación de DNI

- **Registro público.** Pide una autorización explícita (casilla sin marcar) y, al enviar, comprueba que el primer nombre y el primer apellido escritos correspondan al DNI. Nunca devuelve el nombre registrado: el formulario es público y no puede servir para averiguar a quién pertenece un DNI. Si el proveedor no está configurado o no responde, el registro sigue.
- **Alta exprés de emergencia.** Con la autorización del cliente, el personal completa nombre y apellido desde el DNI con un botón. Cada consulta queda en *Movimientos* con quién la hizo y el DNI enmascarado.
- **Proveedor.** Hoy Factiliza (`FACTILIZA_API_KEY`, 100 consultas gratis para empezar). De su respuesta se usan solo nombres y apellidos; dirección y ubigeo se descartan en el adaptador y no llegan a los logs. Apis.net.pe y Decolecta dejaron de ofrecer DNI al público por la Ley 29733.
- **Para producción.** Conviene el convenio con RENIEC (servicio de verificación de identidad, S/ 0.40 a S/ 1.60 por consulta): los proveedores privados no documentan el origen de los datos y el riesgo legal es de la clínica. Cambiar de proveedor es un adaptador nuevo que satisfaga `core/identity_registry.py` y una línea en `get_identity_registry`; ningún caso de uso cambia.

## Carnet de vacunas

Cada vacuna aplicada se registra con fecha, producto, lote y próxima dosis (tabla `pet_vaccinations`, migración 0021). El dueño ve el carnet de su mascota en *Mis mascotas*; el veterinario lo ve y registra desde la ficha del cliente.

- **Catálogo por especie** (`modules/medical_records/domain/vaccination.py`): antirrábica para perros y gatos, séxtuple u óctuple y tos de las perreras para perros, triple felina y leucemia para gatos, desparasitación y "otra vacuna" para cualquiera.
- **Próxima dosis sugerida.** Anual para las vacunas, cada 90 días la desparasitación. La séxtuple y la triple felina van cada 21 días mientras la mascota tiene menos de un año. El veterinario puede cambiar la fecha o dejarla vacía.
- **Estado de cada vacuna** según su última dosis: *Vencida*, *Vence pronto* (30 días o menos), *Al día* o *Sin refuerzo*. El carnet muestra lo más urgente primero.

### Microchip y carnet en PDF

- **Microchip ISO.** Uno nuevo debe tener 15 dígitos (ISO 11784/11785; los tres primeros son el país, 604 para Perú, o el fabricante). Un chip antiguo de 9 o 10 dígitos ya guardado sigue valiendo mientras no se cambie.
- **RENIAN.** Junto al número, "Consultar en RENIAN" copia el microchip y abre su buscador en otra pestaña: RENIAN no tiene API ni acepta el número en la dirección, y leer su web de forma automática no está permitido.
- **Carnet en PDF.** Dueño y personal lo bajan desde el carnet de vacunas: datos de la mascota y del dueño, estado de cada vacuna, aplicaciones con producto y lote, y un código QR.
- **Verificación por QR.** El QR abre `/carnet/<enlace>`, una página pública con la mascota, el microchip y el estado actual de sus vacunas, sin ningún dato del dueño. El enlace va firmado con HMAC (`core/signed_links.py`, clave derivada de `JWT_SECRET_KEY` con un propósito propio) y vence al año; uno alterado o vencido responde igual que uno inexistente. Cambiar `JWT_SECRET_KEY` invalida los carnets ya impresos.

## Asistente de IA (OpenRouter)

El veterinario pide desde la historia clínica un resumen de la mascota antes de la consulta: un texto breve, alertas (alergias, vacunas vencidas, cambios de peso) y pendientes. Se pide a mano, no se guarda y lleva la advertencia de revisarlo.

- **Proveedor.** OpenRouter, con `deepseek/deepseek-v4.1-flash` (US$ 0.15 de entrada y 0.60 de salida por millón de tokens, septiembre de 2026) y `deepseek/deepseek-v4-flash-0731` de respaldo. Un resumen típico consume unos miles de tokens: menos de un décimo de centavo de dólar.
- **Configuración.** `OPENROUTER_API_KEY` en `backend/.env`. Sin clave, el botón responde que el asistente no está configurado y todo lo demás funciona igual. Los modelos se cambian con `OPENROUTER_MODEL` y `OPENROUTER_FALLBACK_MODEL`.
- **Cada petición** pide la respuesta como JSON con forma fija, apaga el razonamiento (se cobraría como salida) y exige proveedores que no guarden los datos para entrenar.
- **Privacidad.** Al modelo llegan la ficha, el carnet y la historia de la mascota; nunca el nombre, el DNI ni el contacto del dueño. Como el proveedor está fuera del Perú, el aviso de privacidad de la clínica debe mencionarlo (Ley 29733).
- **Código.** El puerto es `core/llm.py` y el adaptador `core/llm_openrouter.py`. Las pruebas usan un modelo falso y nunca llaman a OpenRouter.

## WhatsApp Business API — pendiente

El código ya está listo del lado de GestVet. `gestvet.core.whatsapp.WhatsAppSender` es el puerto (un `Protocol`, sin saber nada de negocio) y está conectado en cuatro puntos: confirmar una cita, confirmar un pago por QR, un recordatorio 24 horas antes de la cita y otro una semana antes de la próxima dosis de una vacuna (en horario de atención, una sola vez por dosis y solo por la última aplicación de cada vacuna). Los dos recordatorios corren en un `asyncio.Task` dentro del propio proceso del backend, sin agregar ninguna dependencia nueva ni un servicio aparte. El adaptador de hoy, `ConsoleWhatsAppSender`, registra cada mensaje en el log en vez de mandarlo, así que todo el flujo se prueba completo en desarrollo.

Lo que falta depende de la clínica, no del código:

1. **Elegir el camino**: directo con Meta (Cloud API — gratis salvo el costo por conversación, pero con una verificación de negocio que puede demorar) o vía un intermediario (Twilio, 360dialog, etc. — más rápido de activar, con un costo mensual fijo además del costo por mensaje).
2. **Verificar el negocio** ante Meta con el RUC y los documentos de la clínica.
3. **Dar de alta las plantillas de mensaje** (confirmación de cita, recordatorio de cita, vacuna por vencer, pago confirmado) para que Meta las apruebe: un mensaje fuera de plantilla no se puede mandar fuera de una conversación que el cliente ya inició.
4. **Reemplazar el adaptador**: una clase nueva que satisfaga `WhatsAppSender` llamando a la API real, y una línea a cambiar en `get_whatsapp_sender()` de `appointments/adapters/api/dependencies.py` y de `billing/adapters/api/dependencies.py`, más las dos funciones de `main.py` que arman los recordatorios periódicos. Ningún caso de uso cambia; el puerto es el mismo.

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

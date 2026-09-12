# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Existing and kept: React 19, Vite, TypeScript 6, react-router, TanStack Query, React Hook Form with Zod, Zustand. The backend is FastAPI and the frontend derives its types from the backend's OpenAPI schema.

Binding decision by the user (2026-09-12): the UI is built with **shadcn/ui on Tailwind CSS**, and every table uses **TanStack Table**. shadcn/ui (Radix base) and Tailwind CSS 4 are installed and configured; TanStack Table is installed but no screen uses it yet. The existing screens still use the hand-written CSS in `src/style.css`, kept in a `legacy` cascade layer until they migrate. The theme is shadcn's neutral default; the product's own visual identity is undecided. Adopting shadcn/ui must respect the project's enforced lint rules (file naming, architecture boundaries, no barrel files, comment policy) by adapting configuration, not by adding inline exceptions.

## Users

Two primary audiences with equal priority. When they compete, each surface serves its own user rather than one audience winning globally.

- **Pet owners (clients).** Register their pets, book appointments into a veterinarian's published availability, open an emergency, pay, file complaints with evidence, leave reviews, and follow their pets' clinical history.
- **Clinic staff.** Administration runs staff, clients, payments, complaints, indicators and the activity log. Veterinarians run their agenda, appointments, clinical records and hospitalizations. Emergency veterinarians additionally cover on-call emergencies.

Which device each role uses is not known. Every role must work equally well on a phone and on a desktop computer.

## Product Purpose

GestVet runs a veterinary clinic end to end: accounts and roles, pets and their clinical history, veterinarian availability, appointments and emergencies, payments, complaints, hospitalizations, reviews, and assisted insights for administration.

It is being built to be sold to veterinary clinics. No client clinic is defined yet. Success means a clinic can run its daily operation in it, and its clients can serve themselves without calling the clinic.

## Positioning

Not confirmed with the user. Candidate differentiators present in the codebase, to validate before any marketing surface uses them:

- Booking only inside a veterinarian's published availability, with overlap and a 10-minute turnaround enforced by the server.
- Emergencies opened on the spot and assigned automatically to an on-call veterinarian.
- Assisted insights: care reminders, no-show risk, atypical payments, and veterinarians to watch.

## Operating Context

- Language: Spanish. Locale formatting uses `es-PE`; currency is Peruvian soles.
- Roles: `admin`, `client`, `veterinarian`, `emergency_veterinarian`. Authorization is enforced by the backend on every request; route guards in the UI are a convenience only.
- Main flows: self-registration and sign-in, password recovery, pet registration, booking, emergency (including express intake of a new client by staff), appointment confirmation, completion and cancellation with reason, clinical record with attachments and PDF export, manual and QR payments, complaints with evidence, hospitalizations, reviews, indicators, activity log.
- Alerts exist for veterinarians about emergencies and for clients about their appointments.

## Capabilities and Constraints

- Payment by QR runs on a single simulated adapter. There is no account with a real payment provider yet.
- Password recovery only prints the reset link to the server console. There is no real email delivery yet.
- There is no rate limiting on sign-in or password recovery yet.
- Appointment types and prices seeded by the migrations are sample data, not a real price list.
- Terminology in use: cita, mascota, historia clínica, motivo de consulta, guardia, emergencia, reclamo, internación, reseña, movimientos, indicadores.

## Brand Commitments

- **Product name:** GestVet. Binding.
- **Clinic identity shown to visitors:** "Clínica veterinaria en Trujillo", Av. Prof. César Vallejo 95, Víctor Larco Herrera, Trujillo. The user requires keeping it while no client clinic exists. It is demonstration identity, and a real client's data will replace it.
- **Promotional claims approved by the user:** the clinic is "la clínica líder en la ciudad" and attends "las 24 horas del día". They are marketing copy the user chose to publish, not verified facts, and must be revisited for each real client.

## Evidence on Hand

- No real clinic, customers, testimonials, case studies, clinic photography, logo files, usage metrics, or published price list exist.
- Future work must not fabricate any of those. The approved claims above are the only promotional statements available.

## Product Principles

1. **Both sides are first-class.** Owner self-service and clinic operations get the same level of care; neither is an afterthought of the other.
2. **Phone and desktop are equal targets.** No role is designed desktop-first or mobile-first at the expense of the other.
3. **The server is the authority.** Ownership, roles and scheduling rules live in the backend; the interface explains them and never is the only line of defense.
4. **Accessibility is a requirement.** WCAG 2.2 AA is part of done, not a later polish pass.
5. **Sellable to any clinic.** Clinic identity, contact data and claims are replaceable content, so nothing in the product should depend on one specific clinic.

## Accessibility & Inclusion

WCAG 2.2 AA is mandatory for every surface and every role, on phone and desktop. The interface is in Spanish.

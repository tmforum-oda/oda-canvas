# AGENTS.md — canvas-portal/

Web portal for ODA Canvas management. Multi-module project with a Java Spring Boot backend and Vue.js 3 frontend.

## Architecture

```
canvas-portal/
  pom.xml              # Parent Maven POM (Spring Boot 3.1.5, Java 17)
  portal-core/         # Core library module (shared domain objects)
  portal-service/      # Spring Boot REST service
  portal-helm/         # Helm client integration from Java
  portal-web/          # Vue.js 3 frontend (independent npm project)
  build/               # Build artifacts (gitignored)
  charts/              # Helm chart for portal deployment
```

## Backend (Java/Spring Boot)

### Technology

- Java 17, Spring Boot 3.1.5
- Kubernetes client: `io.fabric8:kubernetes-client:6.5.0`
- Jackson, Lombok, Guava

### Commands

```bash
# Build all Java modules
mvn clean install

# Run Spring Boot service
cd portal-service
mvn spring-boot:run

# Run Java tests
mvn test
```

## Frontend (Vue.js)

The frontend is in `portal-web/` and is **NOT a Maven module** — it has its own npm build system.

### Technology

- Vue 3.3 + Vite
- State management: Pinia
- UI framework: Element Plus + Tailwind CSS
- Code editor: Monaco Editor
- Internationalisation: vue-i18n

### Commands

```bash
cd portal-web
npm install
npm run dev              # Development server (Vite)
npm run build            # Production build
npm run lint             # ESLint + Prettier
npm run format           # Format with Prettier
```

### Source Structure

```
portal-web/src/
  App.vue
  main.js
  components/            # Reusable Vue components
  views/                 # Page-level views
  router/                # Vue Router configuration
  stores/                # Pinia state stores
  layout/                # Layout components
  utils/                 # Helper utilities
  assets/                # Static assets
```

## Do

- Keep frontend and backend builds independent
- Use Element Plus components for UI consistency
- Follow Vue 3 Composition API patterns
- Run `npm run lint` before committing frontend changes

## Don't

- Do not try to build `portal-web/` through Maven — it is a standalone npm project
- Do not commit `build/` or `target/` directories
- Do not use default credentials (`admin/pAssw0rd`) — they are for development only

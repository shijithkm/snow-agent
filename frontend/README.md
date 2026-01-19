# Ops AI Agent - Frontend

Next.js 16.1.2 frontend for the Ops AI Agent ticket automation system.

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Set environment variable (optional)
export NEXT_PUBLIC_API_BASE=http://localhost:8000

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Docker Deployment

From the project root:

```bash
docker-compose up -d --build
```

Access at [http://localhost:3000](http://localhost:3000)

## Features

- 🤖 **Conversational Chat Interface** - Natural language ticket creation
- 📊 **Real-time Dashboard** - Live ticket and alert monitoring (2s refresh)
- 📱 **Mobile Responsive** - Optimized for all screen sizes with hamburger menu
- 🎨 **Dark Theme** - Modern slate-based color palette
- ⚡ **Fast Performance** - Built with Turbopack and React 19

## Technology Stack

- **Framework**: Next.js 16.1.2 (App Router)
- **Runtime**: React 19
- **Language**: TypeScript
- **Styling**: TailwindCSS 3.4
- **Build Tool**: Turbopack

## Project Structure

```
frontend/
├── app/                      # Pages (App Router)
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page
│   ├── chat/                # Chat interface
│   ├── tickets/             # Ticket management
│   └── grafana/             # Alert dashboard
├── components/               # React components
│   ├── Header.tsx           # Navigation (hamburger menu)
│   ├── TicketList.tsx       # Ticket display
│   ├── TicketForm.tsx       # Ticket creation
│   └── AlertList.tsx        # Alert display
├── api.ts                   # Backend API client
└── style/global.css         # Global styles
```

## API Configuration

The frontend uses relative URLs (`/api/*`) that are proxied to the backend through Next.js server configuration.

**next.config.ts**:

```typescript
async rewrites() {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  return [
    {
      source: "/api/:path*",
      destination: `${backendUrl}/:path*`
    }
  ];
}
```

**Docker**: Uses `BACKEND_URL=http://backend:8000` (internal Docker network)  
**Local**: Uses `BACKEND_URL=http://localhost:8000` (default)

## Available Scripts

```bash
npm run dev       # Start development server
npm run build     # Build for production
npm run start     # Start production server
npm run lint      # Run ESLint
```

## Environment Variables

**Development** (`.env.local`):

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000  # Optional, for direct backend calls
```

**Docker** (set in `docker-compose.yml`):

```yaml
build:
  args:
    - BACKEND_URL=http://backend:8000 # Build-time variable
environment:
  - BACKEND_URL=http://backend:8000 # Runtime variable
```

## Documentation

For detailed documentation, see [FRONTEND_DOCUMENTATION.md](../FRONTEND_DOCUMENTATION.md)

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)

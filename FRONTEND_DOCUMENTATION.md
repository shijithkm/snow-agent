# Frontend Documentation - Snow AI Agent

## Overview

The Snow AI Agent frontend is a Next.js 16.1.2 application built with React, TypeScript, and TailwindCSS. It provides a responsive, mobile-friendly interface for ServiceNow ticket management, alert monitoring, and conversational AI interactions.

## Architecture

```
frontend/
├── app/                       # Next.js app router pages
│   ├── layout.tsx            # Root layout with navigation
│   ├── page.tsx              # Home page with agent overview
│   ├── chat/
│   │   └── page.tsx          # Conversational ticket creation
│   ├── tickets/
│   │   ├── list/
│   │   │   └── page.tsx      # Ticket list view
│   │   └── create/
│   │       └── page.tsx      # Form-based ticket creation
│   └── grafana/
│       └── page.tsx          # Grafana alert dashboard
├── components/                # React components
│   ├── Header.tsx            # Navigation header (Client Component)
│   ├── TicketList.tsx        # Ticket list display
│   ├── TicketForm.tsx        # Ticket creation form
│   └── AlertList.tsx         # Alert list display
├── style/
│   └── global.css            # Global styles and Tailwind imports
├── api.ts                    # Backend API client
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # TailwindCSS configuration
└── next.config.ts            # Next.js configuration
```

## Technology Stack

- **Framework**: Next.js 16.1.2 with Turbopack
- **Runtime**: React 19
- **Language**: TypeScript
- **Styling**: TailwindCSS 3.4
- **Build Tool**: Turbopack (development)
- **Routing**: Next.js App Router

## Core Components

### 1. Root Layout (`app/layout.tsx`)

**Purpose**: Root layout wrapper for all pages with navigation header.

**Type**: Server Component (default)

**Structure**:

```tsx
<html lang="en">
  <body>
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-4 sm:py-8">
      <Header />
      {children}
    </div>
  </body>
</html>
```

**Features**:

- Responsive container (max-width: 1024px)
- Dark theme (bg-slate-950)
- Global padding with responsive breakpoints
- Imports global CSS and Header component

---

### 2. Navigation Header (`components/Header.tsx`)

**Purpose**: Responsive navigation header with mobile hamburger menu.

**Type**: Client Component (`"use client"`)

**State**:

```tsx
const [menuOpen, setMenuOpen] = useState(false);
```

**Navigation Links**:

- Home (`/`)
- Chat (`/chat`)
- Ticket List (`/tickets/list`)
- Create Ticket (`/tickets/create`)
- Grafana (`/grafana`)

**Responsive Behavior**:

- **Desktop (≥768px)**: Horizontal navigation bar
- **Mobile (<768px)**: Hamburger menu with dropdown

**Features**:

- Mobile menu toggle button
- Menu closes automatically after navigation
- Hover effects on links
- Dark theme styling
- Accessibility: aria-label on menu button

**Styling**:

```tsx
{
  /* Desktop Navigation */
}
<nav className="hidden md:flex space-x-4">
  <Link href="/" className="text-sm text-slate-300 hover:text-white">
    Home
  </Link>
</nav>;

{
  /* Mobile Menu Button */
}
<button className="md:hidden p-2 rounded-lg bg-slate-800">
  <svg>...</svg>
</button>;

{
  /* Mobile Navigation Dropdown */
}
{
  menuOpen && (
    <nav className="md:hidden mt-4 flex flex-col space-y-2">
      <Link onClick={() => setMenuOpen(false)}>Home</Link>
    </nav>
  );
}
```

---

### 3. Home Page (`app/page.tsx`)

**Purpose**: Landing page with agent information cards and navigation.

**Features**:

- Hero section with title and description
- Quick action buttons (Create Ticket, View Tickets, Chat)
- Agent information cards (Alert Suppression, RFI, L1 Support)
- Responsive grid layout

**Agent Cards**:

1. **Alert Suppression Agent** 🔕
   - Automatically suppresses Grafana alerts
   - Assigns to Snow Agent
   - Closes tickets immediately after configuration

2. **RFI Agent** 🔍
   - Researches information requests
   - Uses web search (Tavily)
   - Provides sourced answers

3. **L1 Support** 👤
   - Routes general support tickets
   - Assigns to L1 Team
   - Manual handling

**Responsive Layout**:

```tsx
{
  /* Button Layout */
}
<div className="flex flex-col sm:flex-row gap-4">
  <button>Create Ticket</button>
  <button>View Tickets</button>
</div>;

{
  /* Grid Layout */
}
<div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Agent cards */}
</div>;
```

**Breakpoints**:

- **Mobile**: Stacked layout, single column
- **Tablet (≥640px)**: 2-column grid
- **Desktop (≥1024px)**: 3-column grid

---

### 4. Chat Interface (`app/chat/page.tsx`)

**Purpose**: Conversational interface for natural language ticket creation.

**Type**: Client Component

**State Management**:

```tsx
const [messages, setMessages] = useState<Message[]>([]);
const [input, setInput] = useState("");
const [sessionId] = useState(() => `session-${Date.now()}`);
const [isLoading, setIsLoading] = useState(false);
```

**Features**:

- Real-time chat interface
- Message history with role-based styling
- Auto-scroll to latest message
- Loading indicator
- Persistent session ID
- Error handling

**Message Flow**:

1. User types message and presses Enter/Send
2. Message added to chat history
3. API request to `/chat` endpoint
4. Assistant response added to history
5. Scroll to latest message

**Message Rendering**:

```tsx
{
  messages.map((msg) => (
    <div
      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[85%] sm:max-w-[80%] rounded-lg p-3 sm:p-4 ${
          msg.role === "user"
            ? "bg-blue-600 text-white"
            : "bg-slate-800 text-slate-100"
        }`}
      >
        {msg.content}
      </div>
    </div>
  ));
}
```

**Responsive Features**:

- Mobile-optimized message bubbles (85% width on mobile, 80% on desktop)
- Responsive padding (p-2 on mobile, p-4 on desktop)
- Smaller text on mobile (text-xs on mobile, text-sm on desktop)
- Responsive height calculation: `h-[calc(100vh-10rem)] sm:h-[calc(100vh-8rem)]`

**Input Controls**:

- Text input with placeholder: "Type your message..."
- Send button (disabled when empty or loading)
- Enter key to send
- Clear input after sending

---

### 5. Ticket List Page (`app/tickets/list/page.tsx`)

**Purpose**: Displays all ServiceNow tickets with real-time updates.

**Type**: Client Component

**State**:

```tsx
const [tickets, setTickets] = useState<any[]>([]);
const [loading, setLoading] = useState(true);
```

**Features**:

- Auto-refresh every 2 seconds
- Loading state indicator
- Delegates rendering to TicketList component
- Error handling

**Lifecycle**:

```tsx
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await getTickets();
    setTickets(Object.values(data));
  }, 2000);
  return () => clearInterval(interval);
}, []);
```

---

### 6. Ticket List Component (`components/TicketList.tsx`)

**Purpose**: Renders ticket list with status badges and details.

**Features**:

- Status-based color coding
- Responsive card layout
- Time window display for silence_alert tickets
- Work comments/research results display
- Agent assignment indicators (🤖 for agents, 👤 for L1)

**Status Badges**:

1. **IN PROGRESS / SUPPRESSING** (🟠)
   - Amber badge with pulsing dot
   - Shows "SUPPRESSING" for silence_alert tickets
   - Shows "IN PROGRESS" for other tickets

2. **SUPPRESSED** (🟣)
   - Purple badge with pulsing dot
   - Special status for suppressed alerts

3. **OPEN** (🟢)
   - Slate badge with green pulsing dot
   - Default status for new tickets

4. **CLOSED** (⚪)
   - Slate badge without animation
   - Final status

**Ticket Card Structure**:

```tsx
<li className="rounded-md bg-slate-950 border p-2 sm:p-3 text-base">
  <div className="flex flex-col sm:flex-row justify-between">
    <div className="flex-1">
      {/* Ticket ID and Description */}
      <div>TKT-1 — suppress alert</div>

      {/* Type */}
      <div>Type: silence_alert</div>

      {/* Assignment */}
      <div>Assigned to: Snow Agent 🤖</div>

      {/* Time Window (for silence_alert) */}
      <div>From: 1/17/2026, 10:00 AM — To: 1/17/2026, 11:00 AM</div>
    </div>

    {/* Status Badge */}
    <div>
      <span className="bg-amber-700/10 text-amber-300">SUPPRESSING</span>
    </div>
  </div>

  {/* Work Comments (Research Results) */}
  {work_comments && (
    <div className="mt-3 bg-slate-900 border p-2">
      <div>🔍 Research Results</div>
      <pre>{work_comments}</pre>
    </div>
  )}
</li>
```

**Font Sizes** (Enhanced for readability):

- Container: `text-base`
- Type/Assignment: `text-sm`
- Time: `text-sm`
- Status badges: `text-sm`
- Work comments header: `text-sm sm:text-base`
- Work comments content: `text-sm`

**Responsive Features**:

- Stacked layout on mobile (flex-col)
- Side-by-side on desktop (sm:flex-row)
- Responsive padding (p-2 on mobile, sm:p-3)
- Text wrapping for long descriptions (break-words)
- Horizontal scroll for code blocks (overflow-x-auto)

---

### 7. Create Ticket Page (`app/tickets/create/page.tsx`)

**Purpose**: Form-based ticket creation interface.

**Type**: Client Component

**Features**:

- Delegates to TicketForm component
- Simple wrapper page

---

### 8. Ticket Form Component (`components/TicketForm.tsx`)

**Purpose**: Form for creating tickets with alert selection.

**State**:

```tsx
const [description, setDescription] = useState("");
const [alerts, setAlerts] = useState<any[]>([]);
const [selectedAlert, setSelectedAlert] = useState<string | null>(null);
const [isSubmitting, setIsSubmitting] = useState(false);
```

**Fields**:

1. **Description**: Text input for ticket description
2. **Alert Selection**: Dropdown with available alerts (optional)

**Form Flow**:

1. Fetch alerts on mount
2. User enters description
3. User optionally selects alert
4. Submit calls `processTicket(description, alert_id)`
5. Success: Show confirmation and refresh tickets
6. Error: Show error message

**Validation**:

- Description required (min length check)
- Submit button disabled when submitting

**Styling**:

- Dark theme form elements
- Hover effects on buttons
- Disabled state styling
- Responsive padding

---

### 9. Grafana Page (`app/grafana/page.tsx`)

**Purpose**: Grafana alert dashboard with real-time updates.

**Type**: Client Component

**Features**:

- Auto-refresh every 2 seconds
- Loading state
- Delegates to AlertList component

---

### 10. Alert List Component (`components/AlertList.tsx`)

**Purpose**: Displays Grafana alerts with status indicators.

**Features**:

- Status-based color coding
- Responsive card layout
- Status icons and badges

**Status Display**:

1. **Firing** (🔴)
   - Red badge
   - Indicates active alert

2. **Silenced** (🔕)
   - Gray badge
   - Shows suppression window if available
   - Format: "Silenced from X to Y"

3. **OK** (✅)
   - Green badge
   - Normal status

**Alert Card Structure**:

```tsx
<li className="rounded-md bg-slate-950 border p-3 flex justify-between">
  <div>
    <div className="font-semibold">CPU High</div>
    <div className="text-sm">ID: A-1</div>
    {silenced_from && silenced_until && (
      <div className="text-xs">
        Silenced from {time} to {time}
      </div>
    )}
  </div>
  <div>
    <span className="px-2 py-1 rounded bg-red-700/10 text-red-300">FIRING</span>
  </div>
</li>
```

---

## API Client (`api.ts`)

**Purpose**: Centralized API communication layer with Docker-aware URL handling.

**Base URL Configuration**:

```typescript
// Use relative URLs to go through Next.js server proxy in Docker
// In dev mode, can still use direct backend URL
export const API_BASE =
  typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_BASE
    ? process.env.NEXT_PUBLIC_API_BASE
    : "/api";
```

**Docker Architecture**:

- **Browser Requests**: Use relative URLs (`/api/*`) that go through Next.js server
- **Next.js Server Proxy**: Configured in `next.config.ts` to forward to backend
- **Backend URL**: `http://backend:8000` (Docker internal network) or `http://localhost:8000` (local dev)

**Next.js Rewrite Configuration** (`next.config.ts`):

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

**Functions**:

### `getAlerts()`

Fetches all Grafana alerts.

**Returns**:

```typescript
Promise<
  Array<{
    id: string;
    name: string;
    status: "firing" | "silenced" | "ok";
    silenced_from?: string;
    silenced_until?: string;
  }>
>;
```

### `getTickets()`

Fetches all ServiceNow tickets.

**Returns**:

```typescript
Promise<{
  [ticketId: string]: {
    id: string;
    description: string;
    status: "open" | "in_progress" | "closed" | "suppressed";
    assigned_to?: string;
    work_comments?: string;
    ticket_type?: string;
    alert_id?: string;
    start_time?: string;
    end_time?: string;
  };
}>;
```

### `processTicket(description, alert_id?)`

Creates and processes a ticket.

**Parameters**:

- `description`: Ticket description
- `alert_id`: Optional alert ID

**Returns**:

```typescript
Promise<{ ticket_id: string }>;
```

### `sendChatMessage(session_id, message)`

Sends chat message and receives response.

**Parameters**:

- `session_id`: Unique session identifier
- `message`: User message text

**Returns**:

```typescript
Promise<{
  reply: string;
  ticket_created: boolean;
  ticket_id?: string;
}>;
```

### `getChatHistory(session_id)`

Retrieves chat conversation history.

**Parameters**:

- `session_id`: Session identifier

**Returns**:

```typescript
Promise<{
  messages: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
}>;
```

---

## Styling System

### TailwindCSS Configuration

**Colors** (Dark Theme):

- Background: `slate-950` (main), `slate-900` (cards), `slate-800` (elements)
- Text: `slate-100` (primary), `slate-300` (secondary), `slate-400` (muted)
- Accents: `blue-600`, `amber-300`, `purple-300`, `red-300`, `green-300`

**Responsive Breakpoints**:

```javascript
{
  sm: '640px',   // Small devices (tablets)
  md: '768px',   // Medium devices (small laptops)
  lg: '1024px',  // Large devices (desktops)
  xl: '1280px',  // Extra large devices
}
```

**Common Patterns**:

#### Responsive Padding

```tsx
className = "p-2 sm:p-3 md:p-4";
```

#### Responsive Text Size

```tsx
className = "text-xs sm:text-sm md:text-base";
```

#### Responsive Layout

```tsx
className = "flex flex-col sm:flex-row";
```

#### Responsive Grid

```tsx
className = "grid sm:grid-cols-2 lg:grid-cols-3";
```

### Global Styles (`style/global.css`)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #1e293b; /* slate-900 */
}

::-webkit-scrollbar-thumb {
  background: #475569; /* slate-600 */
  border-radius: 4px;
}
```

---

## Next.js Configuration

### App Router

The application uses Next.js 13+ App Router with the following structure:

- Server Components by default (better performance)
- Client Components where interactivity needed (`"use client"`)
- File-based routing in `app/` directory

### TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "jsx": "preserve",
    "module": "esnext",
    "moduleResolution": "bundler",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### Build Configuration

**Development**:

- Turbopack for fast hot module replacement
- Port: 3000 (or next available)

**Production**:

- Optimized bundle with tree-shaking
- Static optimization for non-dynamic pages

---

## Mobile Responsiveness

### Design Philosophy

**Mobile-First**: All components designed for mobile, then enhanced for desktop.

### Responsive Components

#### 1. Header Navigation

- **Mobile**: Hamburger menu with vertical dropdown
- **Desktop**: Horizontal navigation bar

#### 2. Home Page

- **Mobile**: Stacked buttons, single-column grid
- **Tablet**: 2-column grid
- **Desktop**: 3-column grid

#### 3. Chat Interface

- **Mobile**: Compact padding, smaller text, 85% bubble width
- **Desktop**: More padding, larger text, 80% bubble width

#### 4. Ticket List

- **Mobile**: Stacked layout, vertical cards
- **Desktop**: Side-by-side elements, horizontal layout

#### 5. Forms

- **Mobile**: Full-width inputs, stacked buttons
- **Desktop**: Optimized spacing

### Touch Targets

All interactive elements meet minimum touch target size:

- Buttons: min 44x44px
- Links: min 44x44px padding area
- Form inputs: min 44px height

---

## State Management

### Local State

All components use React `useState` for local state:

- Form inputs
- Loading states
- Modal visibility
- Menu toggles

### Shared State

**No global state management** - components fetch data independently.

**Rationale**:

- Simple architecture
- Real-time auto-refresh keeps data fresh
- No complex state synchronization needed

### Data Fetching Patterns

#### Polling Pattern (Tickets, Alerts)

```tsx
useEffect(() => {
  const fetchData = async () => {
    const data = await getTickets();
    setTickets(Object.values(data));
  };

  fetchData(); // Initial fetch
  const interval = setInterval(fetchData, 2000); // Poll every 2s

  return () => clearInterval(interval); // Cleanup
}, []);
```

#### Request-Response Pattern (Chat)

```tsx
const handleSend = async () => {
  setMessages([...messages, userMessage]);
  const response = await sendChatMessage(sessionId, input);
  setMessages([...messages, userMessage, assistantMessage]);
};
```

---

## Performance Optimizations

### 1. Server Components

Default to Server Components for:

- Static content (Home page)
- Layout wrappers
- Non-interactive elements

Benefits:

- Smaller client-side JavaScript bundle
- Faster initial page load
- Better SEO

### 2. Client Components

Use Client Components only for:

- Interactive elements (forms, buttons)
- State management
- Real-time updates

### 3. Code Splitting

Next.js automatically code-splits by page:

- Only load JavaScript needed for current page
- Lazy load other routes

### 4. Image Optimization

Use Next.js `<Image>` component for:

- Automatic image optimization
- Responsive images
- Lazy loading

### 5. Caching

Browser caches API responses:

- Short TTL for real-time data
- Longer TTL for static data

---

## Accessibility

### ARIA Labels

```tsx
<button aria-label="Toggle menu">
  <svg>...</svg>
</button>
```

### Semantic HTML

- Use proper heading hierarchy (h1, h2, h3)
- Use `<nav>` for navigation
- Use `<button>` for clickable actions
- Use `<form>` for form submissions

### Keyboard Navigation

- All interactive elements keyboard accessible
- Tab order follows visual order
- Enter key submits forms
- Escape key closes modals

### Color Contrast

All text meets WCAG AA standards:

- Background: `slate-950`
- Primary text: `slate-100` (high contrast)
- Secondary text: `slate-300` (medium contrast)
- Muted text: `slate-400` (low contrast)

---

## Environment Variables

### Required Variables

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000  # Backend API URL
```

### Usage

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
```

**Note**: Variables must be prefixed with `NEXT_PUBLIC_` to be accessible in browser.

---

## Deployment

### Development

```bash
cd frontend
npm install
npm run dev
```

**URL**: http://localhost:3000

### Production Build

```bash
npm run build
npm start
```

### Docker

```bash
cd frontend
docker build -t snow-ai-agent-frontend .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE=http://backend:8000 \
  snow-ai-agent-frontend
```

---

## Error Handling

### API Errors

```tsx
try {
  const data = await getTickets();
  setTickets(data);
} catch (error) {
  console.error("Failed to fetch tickets:", error);
  // Show error message to user
}
```

### Network Errors

- Display user-friendly error messages
- Retry logic for transient failures
- Graceful degradation

### Loading States

```tsx
{
  loading ? <div>Loading...</div> : <TicketList tickets={tickets} />;
}
```

---

## Browser Support

### Supported Browsers

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

### Polyfills

Next.js includes polyfills for:

- Promise
- Fetch API
- Object.assign
- Array methods

---

## Testing

### Manual Testing Checklist

#### Desktop

- [ ] Navigate between all pages
- [ ] Create ticket via form
- [ ] Create ticket via chat
- [ ] View ticket list with auto-refresh
- [ ] View Grafana alerts
- [ ] Test all alert suppression flows

#### Mobile

- [ ] Open hamburger menu
- [ ] Navigate between pages from menu
- [ ] Menu closes after navigation
- [ ] Chat interface usable
- [ ] Ticket cards readable
- [ ] Forms submittable

#### Responsive

- [ ] Resize browser window
- [ ] Test all breakpoints (640px, 768px, 1024px)
- [ ] Check text wrapping
- [ ] Verify no horizontal scroll

---

## Docker Deployment

### Configuration

The frontend is containerized using Docker with multi-stage build for production optimization.

**Dockerfile**:

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Accept build argument for backend URL
ARG BACKEND_URL=http://localhost:8000
ENV BACKEND_URL=$BACKEND_URL

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

**Docker Compose Configuration**:

```yaml
frontend:
  build:
    context: ./frontend
    args:
      - BACKEND_URL=http://backend:8000 # Docker internal network URL
  container_name: snow-ai-frontend
  ports:
    - "3000:3000"
  environment:
    - BACKEND_URL=http://backend:8000 # Runtime environment variable
  networks:
    - app-network
  depends_on:
    - backend
```

### Build Process

```bash
# Build and start containers
docker-compose up -d --build

# Rebuild specific service
docker-compose build --no-cache frontend

# View logs
docker-compose logs -f frontend
```

### Environment Variables

**Build Time (ARG)**:

- `BACKEND_URL`: Used during `npm run build` for Next.js rewrites configuration

**Runtime (ENV)**:

- `BACKEND_URL`: Available to Next.js server for dynamic configuration

### Network Architecture

```
Browser → http://localhost:3000 → Frontend Container (Next.js)
                                        ↓
                                   Proxy /api/* requests
                                        ↓
                                   http://backend:8000 (Docker network)
                                        ↓
                                   Backend Container (FastAPI)
```

**Key Points**:

- Browser accesses frontend on `localhost:3000`
- Frontend container proxies API requests to backend using Docker service name
- Backend is accessible at `http://backend:8000` within Docker network
- No CORS issues since browser only talks to frontend

### Troubleshooting Docker

**"Failed to proxy http://localhost:8000"**:

- Backend URL not properly configured in Next.js rewrites
- Solution: Verify `BACKEND_URL` build arg is set in docker-compose.yml

**"ECONNREFUSED" in logs**:

- Backend container not running or not accessible
- Solution: Check `docker ps`, ensure backend is up, check network with `docker network inspect`

**Build cache issues**:

```bash
docker-compose build --no-cache frontend
docker-compose up -d
```

---

## Common Issues & Solutions

### Issue: "ChunkLoadError"

**Cause**: Stale Next.js build cache

**Solution**:

```bash
rm -rf .next
npm run dev
```

### Issue: "Port 3000 in use"

**Cause**: Another process using port 3000

**Solution**: Next.js automatically uses next available port (3001, 3002, etc.)

### Issue: "Cannot connect to backend"

**Cause**: Backend not running or wrong API_BASE URL

**Solution**:

```bash
# Check backend is running
curl http://localhost:8000/alerts

# Check environment variable
echo $NEXT_PUBLIC_API_BASE
```

### Issue: "Menu doesn't close on mobile"

**Cause**: onClick handler not setting menuOpen to false

**Solution**: Verify Header.tsx has:

```tsx
<Link onClick={() => setMenuOpen(false)}>
```

---

## Future Enhancements

1. **Real-time Updates**: WebSocket for live ticket updates (no polling)
2. **Advanced Search**: Filter and search tickets
3. **Ticket Details Modal**: Detailed view without navigation
4. **File Uploads**: Attach files to tickets
5. **Rich Text Editor**: Markdown support for descriptions
6. **Notifications**: Toast notifications for ticket updates
7. **Dark/Light Mode Toggle**: User preference
8. **Accessibility Improvements**: Screen reader optimization
9. **Internationalization**: Multi-language support
10. **Progressive Web App**: Offline support, install prompt

---

## Contact & Support

For questions or issues, please refer to the main project README or contact the development team.

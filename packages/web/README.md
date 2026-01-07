# Shelly Manager Web UI

A modern, responsive web interface for managing Shelly IoT devices built with React, TypeScript, and Vite.

## ✨ Features

- **🔍 Device Discovery**: Scan and discover Shelly devices on your network
- **⚡ Real-time Updates**: Live device status and firmware management
- **📊 Bulk Operations**: Perform actions on multiple devices simultaneously
- **🔧 Device Management**: Update firmware, reboot devices, and manage configurations

## 🛠️ Tech Stack

- **Frontend Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: shadcn/ui with Tailwind CSS
- **State Management**: TanStack Query (React Query v5)
- **Forms**: React Hook Form with Zod validation
- **Tables**: TanStack Table
- **Routing**: React Router v6
- **Icons**: Lucide React
- **Deployment**: Docker with Nginx

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Access to Shelly Manager API

### Installation

1. Install dependencies:

```bash
npm install
```

2. Create environment file:

```bash
cp env.example .env.local
```

3. Configure your API endpoint in `.env.local`:

```env
VITE_BASE_API_URL=http://localhost:8000
```

4. Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## 📝 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t shelly-manager-web --build-arg VITE_BASE_API_URL=http://your-api-url:8000 .
```

### Run Container

```bash
docker run -p 3000:80 shelly-manager-web
```

### Docker Compose

```yaml
version: "3.8"
services:
  web:
    build:
      context: .
      args:
        VITE_BASE_API_URL: http://api:8000
    ports:
      - "3000:80"
    depends_on:
      - api
```

## 🎨 UI Components

The application uses shadcn/ui components for a consistent, accessible design:

- **Forms**: React Hook Form with Zod validation
- **Tables**: Feature-rich data tables with sorting, filtering, and pagination
- **Dialogs**: Modal dialogs for confirmations and bulk operations
- **Theme**: System/light/dark mode with smooth transitions
- **Toast**: Beautiful notifications for user feedback

## 📡 API Integration

The web interface communicates with the Shelly Manager API for:

- Device discovery and scanning
- Device status monitoring
- Firmware updates
- Device configuration
- Bulk operations

All API calls are managed through TanStack Query for optimal caching and error handling.

## 🌐 Internationalization

The application supports internationalization using react-i18next:

- All user-facing strings are externalized
- Easy to add new languages
- Currently supports English (en)

## 🔧 Configuration

### Environment Variables

- `VITE_BASE_API_URL`: Base URL of the Shelly Manager API (required)

### Local Storage Settings

User preferences are stored in localStorage:

- Theme preference
- Table pagination settings
- Column visibility preferences

## 📱 Responsive Design

The interface is fully responsive and optimized for:

- **Desktop**: Full-featured interface with multi-column layouts
- **Tablet**: Optimized spacing and touch-friendly controls
- **Mobile**: Compact navigation and single-column layouts

## 🔒 Security

- CSP headers configured in nginx
- XSS protection
- No sensitive data stored in localStorage
- Environment-based API configuration
- **Credential Management**: Device passwords stored encrypted on backend
  - Requires `SHELLY_SECRET_KEY` environment variable on API server
  - Passwords never exposed in UI or API responses
  - Credentials Manager UI for adding/removing device passwords

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for all new code
3. Add appropriate error handling
4. Test on multiple screen sizes
5. Update documentation as needed

## 📄 License

MIT License - see the [LICENSE](../../LICENSE) file for details.

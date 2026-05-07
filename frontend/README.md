# OVM - Order & Vendor Management System

Production-grade frontend foundation for the OVM platform.

## 🧱 Tech Stack

- **Framework:** [React 19](https://react.dev/)
- **Build Tool:** [Vite 6](https://vitejs.dev/)
- **Language:** [TypeScript](https://www.typescriptlang.org/) (Strict Mode)
- **Styling:** [Tailwind CSS v4](https://tailwindcss.com/)
- **Linting:** [ESLint](https://eslint.org/)
- **Formatting:** [Prettier](https://prettier.io/)

## 📂 Project Structure

```text
src/
├── api/          # API services and clients
├── app/          # App-wide providers and configuration
├── components/   # Shared UI components
├── hooks/        # Custom React hooks
├── layouts/      # Page layout components
├── routes/       # Route definitions and navigation logic
├── store/        # State management (Zustand, Redux, etc.)
├── styles/       # Global styles and Tailwind configuration
├── types/        # Global TypeScript types and interfaces
├── utils/        # Helper functions and utilities
└── modules/      # Feature-based modules (Domain-driven)
```

## 🚀 Getting Started

### Prerequisites

- Node.js (Latest LTS recommended)
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

## 🛠 Configuration

- **TypeScript:** Strict configuration in `tsconfig.app.json`.
- **Tailwind CSS:** Configured via `@theme` in `src/styles/globals.css`.
- **ESLint:** Modular configuration in `eslint.config.js`.
- **Prettier:** Formatting rules in `.prettierrc`.

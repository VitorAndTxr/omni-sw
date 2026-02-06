---
name: react-component-scaffold
description: |
  Scaffold React/TypeScript components with proper structure. Use when: creating new components,
  setting up component folders, generating boilerplate, or user says "create component", "scaffold",
  "new component", "component structure", "generate component".
---

# React Component Scaffold

## Standard Structure

```
ComponentName/
├── ComponentName.tsx        # Component logic
├── ComponentName.types.ts   # TypeScript interfaces
├── ComponentName.css        # Styles (or .module.css)
├── ComponentName.stories.tsx # Storybook (optional)
├── ComponentName.test.tsx   # Tests (optional)
└── index.ts                 # Barrel export
```

## Quick Scaffold

Run the scaffold script or create files manually:

```bash
# Using script
node scripts/scaffold-component.js ComponentName path/to/components
```

## Templates

### ComponentName.tsx
```typescript
import { FC } from 'react';
import { ComponentNameProps } from './ComponentName.types';
import './ComponentName.css';

export const ComponentName: FC<ComponentNameProps> = ({
  variant = 'default',
  className = '',
  children,
  ...props
}) => {
  return (
    <div
      className={`component-name component-name--${variant} ${className}`.trim()}
      {...props}
    >
      {children}
    </div>
  );
};
```

### ComponentName.types.ts
```typescript
import { HTMLAttributes, ReactNode } from 'react';

export type ComponentNameVariant = 'default' | 'primary' | 'secondary';

export interface ComponentNameProps extends HTMLAttributes<HTMLDivElement> {
  variant?: ComponentNameVariant;
  children?: ReactNode;
}
```

### ComponentName.css
```css
.component-name {
  /* Base styles */
}

.component-name--default {
  /* Default variant */
}

.component-name--primary {
  /* Primary variant */
}
```

### index.ts
```typescript
export { ComponentName } from './ComponentName';
export type { ComponentNameProps, ComponentNameVariant } from './ComponentName.types';
```

### ComponentName.stories.tsx (Storybook)
```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { ComponentName } from './index';

const meta = {
  title: 'Components/ComponentName',
  component: ComponentName,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
} satisfies Meta<typeof ComponentName>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { children: 'Content' },
};

export const Primary: Story = {
  args: { variant: 'primary', children: 'Primary' },
};
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Component | PascalCase | `UserProfile` |
| Props | PascalCase + Props | `UserProfileProps` |
| CSS class | kebab-case | `user-profile` |
| Hook | camelCase + use | `useUserProfile` |
| Context | PascalCase + Context | `UserContext` |

## Checklist

- [ ] TypeScript strict (no `any`)
- [ ] Props interface extends HTML attributes
- [ ] Default prop values in destructuring
- [ ] Barrel export in index.ts
- [ ] CSS follows BEM-like naming
- [ ] Accessible (ARIA when needed)

#!/usr/bin/env node
/**
 * React Component Scaffold Script
 * Usage: node scaffold-component.js ComponentName [path/to/components]
 */

const fs = require('fs');
const path = require('path');

const componentName = process.argv[2];
const targetDir = process.argv[3] || './src/components';

if (!componentName) {
  console.error('Usage: node scaffold-component.js ComponentName [path/to/components]');
  process.exit(1);
}

const componentDir = path.join(targetDir, componentName);

// Templates
const templates = {
  tsx: `import { FC } from 'react';
import { ${componentName}Props } from './${componentName}.types';
import './${componentName}.css';

export const ${componentName}: FC<${componentName}Props> = ({
  variant = 'default',
  className = '',
  children,
  ...props
}) => {
  return (
    <div
      className={\`${componentName.toLowerCase()} ${componentName.toLowerCase()}--\${variant} \${className}\`.trim()}
      {...props}
    >
      {children}
    </div>
  );
};
`,

  types: `import { HTMLAttributes, ReactNode } from 'react';

export type ${componentName}Variant = 'default' | 'primary' | 'secondary';

export interface ${componentName}Props extends HTMLAttributes<HTMLDivElement> {
  /** Component visual variant */
  variant?: ${componentName}Variant;
  /** Content to render inside the component */
  children?: ReactNode;
}
`,

  css: `.${componentName.toLowerCase()} {
  /* Base styles */
}

.${componentName.toLowerCase()}--default {
  /* Default variant */
}

.${componentName.toLowerCase()}--primary {
  /* Primary variant */
}

.${componentName.toLowerCase()}--secondary {
  /* Secondary variant */
}
`,

  index: `export { ${componentName} } from './${componentName}';
export type { ${componentName}Props, ${componentName}Variant } from './${componentName}.types';
`,

  stories: `import type { Meta, StoryObj } from '@storybook/react';
import { ${componentName} } from './index';

const meta = {
  title: 'Components/${componentName}',
  component: ${componentName},
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'primary', 'secondary'],
    },
  },
} satisfies Meta<typeof ${componentName}>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: '${componentName} Content',
  },
};

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary ${componentName}',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary ${componentName}',
  },
};
`,

  test: `import { render, screen } from '@testing-library/react';
import { ${componentName} } from './index';

describe('${componentName}', () => {
  it('renders children correctly', () => {
    render(<${componentName}>Test Content</${componentName}>);
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('applies variant class', () => {
    const { container } = render(
      <${componentName} variant="primary">Content</${componentName}>
    );
    expect(container.firstChild).toHaveClass('${componentName.toLowerCase()}--primary');
  });

  it('applies custom className', () => {
    const { container } = render(
      <${componentName} className="custom-class">Content</${componentName}>
    );
    expect(container.firstChild).toHaveClass('custom-class');
  });
});
`,
};

// Create directory
if (!fs.existsSync(componentDir)) {
  fs.mkdirSync(componentDir, { recursive: true });
}

// Create files
const files = [
  { name: `${componentName}.tsx`, content: templates.tsx },
  { name: `${componentName}.types.ts`, content: templates.types },
  { name: `${componentName}.css`, content: templates.css },
  { name: 'index.ts', content: templates.index },
  { name: `${componentName}.stories.tsx`, content: templates.stories },
  { name: `${componentName}.test.tsx`, content: templates.test },
];

files.forEach(({ name, content }) => {
  const filePath = path.join(componentDir, name);
  fs.writeFileSync(filePath, content);
  console.log(`Created: ${filePath}`);
});

console.log(`\n✅ Component ${componentName} scaffolded at ${componentDir}`);
console.log('\nNext steps:');
console.log('1. Implement component logic');
console.log('2. Add styles');
console.log('3. Run Storybook to preview');

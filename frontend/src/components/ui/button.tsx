import React from 'react';
import { Button as ShadcnButton } from 'shadcn-ui';

const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ children, ...props }) => {
  return (
    <ShadcnButton {...props}>
      {children}
    </ShadcnButton>
  );
};

export default Button;
import React from 'react';

interface SelectProps {
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  value: string;
  label?: string;
}

const Select: React.FC<SelectProps> = ({ options, onChange, value, label }) => {
  return (
    <div className="select-container">
      {label && <label className="select-label">{label}</label>}
      <select className="select-dropdown" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};

export default Select;
import React from 'react';

const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-gray-800 text-white p-4">
      <h2 className="text-lg font-bold mb-4">CV Creator</h2>
      <nav>
        <ul>
          <li className="mb-2">
            <a href="/" className="hover:underline">Home</a>
          </li>
          <li className="mb-2">
            <a href="/editor" className="hover:underline">Editor</a>
          </li>
          <li className="mb-2">
            <a href="/templates" className="hover:underline">Templates</a>
          </li>
          <li className="mb-2">
            <a href="/preview" className="hover:underline">Preview</a>
          </li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
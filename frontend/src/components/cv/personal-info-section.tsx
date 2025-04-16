import React from 'react';

const PersonalInfoSection: React.FC = () => {
  return (
    <div className="personal-info-section">
      <h2>Personal Information</h2>
      <form>
        <div>
          <label htmlFor="name">Name</label>
          <input type="text" id="name" name="name" required />
        </div>
        <div>
          <label htmlFor="email">Email</label>
          <input type="email" id="email" name="email" required />
        </div>
        <div>
          <label htmlFor="phone">Phone</label>
          <input type="tel" id="phone" name="phone" required />
        </div>
        <div>
          <label htmlFor="address">Address</label>
          <input type="text" id="address" name="address" />
        </div>
      </form>
    </div>
  );
};

export default PersonalInfoSection;
import React from 'react';

const EducationSection: React.FC = () => {
    return (
        <div>
            <h2>Education</h2>
            <form>
                <div>
                    <label htmlFor="degree">Degree:</label>
                    <input type="text" id="degree" name="degree" required />
                </div>
                <div>
                    <label htmlFor="institution">Institution:</label>
                    <input type="text" id="institution" name="institution" required />
                </div>
                <div>
                    <label htmlFor="startYear">Start Year:</label>
                    <input type="number" id="startYear" name="startYear" required />
                </div>
                <div>
                    <label htmlFor="endYear">End Year:</label>
                    <input type="number" id="endYear" name="endYear" required />
                </div>
                <button type="submit">Add Education</button>
            </form>
        </div>
    );
};

export default EducationSection;
# Additional Profile Fields for Template Compatibility

After examining both the FAANG and Wenneker CV templates, I've identified several additional fields that should be added to the Profile page to ensure full compatibility with both templates.

## Fields to Add to the Profile

### Professional Information

1. **Job Title / Current Position**
   - Currently missing in the Profile
   - Used in Wenneker CV template as "cvsubheading"
   - Implementation: Add a field for "Current Position" or "Job Title"

2. **Address (Multi-line)**
   - Currently only has "location" (city, country)
   - Wenneker CV template has a structured address with multiple lines
   - Implementation: Add fields for address line 1, address line 2, city, state/province, and postal code

### Projects Section Enhancement

1. **Project URLs & Links**
   - The model has project URLs, but the Profile UI doesn't have fields for them
   - Both templates support links to projects
   - Implementation: Enhance project section UI to add URL fields

### Additional Sections

1. **Interests / Hobbies**
   - Wenneker CV has a dedicated "Interests" section (both professional and personal)
   - Implementation: Add a new section for interests/hobbies with two categories

2. **Awards / Achievements**
   - Wenneker CV has a dedicated "Awards" section
   - Implementation: Add a section for awards and achievements

3. **Communication Skills / Presentations**
   - Wenneker CV has a "Communication Skills" section (presentations, public speaking)
   - Implementation: Add a section for presentations, talks, or communication achievements

### Technical Skills Enhancement

1. **Categorized Skills**
   - FAANG template has categorized skills (Technical, Soft, Other)
   - Wenneker template has categorized skills (Programming, Computer Software)
   - Implementation: Add skill categorization functionality

## Implementation Plan

1. Update the database model (backend/app/models/candidate.py) to include:
   - job_title field
   - address fields (structured as JSON)
   - interests field (as JSON array)
   - awards field (as JSON array)
   - presentations field (as JSON array)

2. Update the Pydantic schemas (backend/app/schemas/candidate.py) to match these new fields

3. Update the Profile page UI to include:
   - New form sections for the added fields
   - Enhanced project entry UI with URL field
   - Skill categories input
   - Address input fields

## Integration with Templates

When generating CVs with these templates:

1. **FAANG Template**
   - Populate the "OBJECTIVE" section with job title and summary
   - Use categorized skills in the "SKILLS" table
   - Use projects with URLs for the "PROJECTS" section

2. **Wenneker CV Template**
   - Use photo for the sidebar image
   - Use structured address in the sidebar
   - Use job_title for the "cvsubheading"
   - Populate the "Interests", "Awards", and "Communication Skills" sections
   - Use categorized skills in the "Software Development Skills" section

This enhancement will ensure that both templates can be fully populated with the user's profile information, providing a better user experience when switching between templates.
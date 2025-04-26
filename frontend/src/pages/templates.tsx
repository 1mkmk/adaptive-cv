import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { getTemplates, Template } from '@/services/templateService';
import { useNavigate } from 'react-router';

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [defaultTemplateId, setDefaultTemplateId] = useState<string | null>(() => {
    return localStorage.getItem('defaultTemplateId');
  });
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();
  
  // Load templates on component mount
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        setLoading(true);
        const templatesData = await getTemplates();
        setTemplates(templatesData);
        
        // If no default template is set but we have templates, set the first one as default
        if (!defaultTemplateId && templatesData.length > 0) {
          setDefaultTemplateId(templatesData[0].id);
          localStorage.setItem('defaultTemplateId', templatesData[0].id);
        }
        
        setError(null);
      } catch (err) {
        console.error('Failed to load templates:', err);
        setError('Failed to load templates. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    loadTemplates();
  }, [defaultTemplateId]);

  const handleUseTemplate = (templateId: string) => {
    // Navigate to the Jobs page with the selected template
    navigate('/jobs', { state: { selectedTemplateId: templateId } });
  };
  
  const handleSetAsDefault = (templateId: string) => {
    // Set the template as default in localStorage
    localStorage.setItem('defaultTemplateId', templateId);
    setDefaultTemplateId(templateId);
    
    // Show success message
    setSuccessMessage(`Template set as default!`);
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      setSuccessMessage(null);
    }, 3000);
  };

  return (
    <>
      <div className="container mx-auto py-10">
        <h1 className="text-3xl font-bold mb-2">CV Templates</h1>
        <p className="text-muted-foreground mb-8">
          Choose from our collection of LaTeX CV templates to generate your personalized CV.
        </p>

        {error && (
          <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-md">
            {error}
          </div>
        )}
        
        {successMessage && (
          <div className="mb-6 p-4 bg-green-500/10 text-green-600 rounded-md">
            {successMessage}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
          </div>
        ) : (
          <>
            {/* Templates Grid */}
            <h2 className="text-2xl font-semibold mb-4">Available Templates</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.map(template => (
                <Card 
                  key={template.id} 
                  className={`overflow-hidden ${template.id === defaultTemplateId ? 'border-green-500 border-2' : ''}`}
                >
                  
                  {/* Template Preview Image */}
                  <div className="aspect-[4/3] w-full bg-muted/30 overflow-hidden">
                    {template.preview ? (
                      <img
                        src={template.preview}
                        alt={`${template.name} preview`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                        No preview available
                      </div>
                    )}
                  </div>
                  
                  <CardHeader>
                    <CardTitle>{template.name}</CardTitle>
                  </CardHeader>
                  
                  <CardFooter className="flex justify-between">
                    <Button 
                      variant="outline"
                      onClick={() => handleSetAsDefault(template.id)}
                    >
                      Select
                    </Button>
                    <Button 
                      onClick={() => handleUseTemplate(template.id)}
                    >
                      Use Template
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
            
            {templates.length === 0 && (
              <div className="text-center py-10">
                <p className="text-muted-foreground">No templates available. Please check back later.</p>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
};

export default Templates;
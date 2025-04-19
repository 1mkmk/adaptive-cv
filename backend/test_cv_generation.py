"""
Script to test CV generation
"""
from app.services.cv_service import generate_cv_with_template
from app.database import SessionLocal

def test_cv_generation():
    """Test generating a CV from template"""
    db = SessionLocal()
    try:
        print("Starting CV generation test...")
        result = generate_cv_with_template(db, 1)
        print(f"CV generation successful. Result keys: {result.keys()}")
        
        if result.get("latex_path"):
            print(f"LaTeX path: {result['latex_path']}")
        
        if result.get("pdf_path"):
            print(f"PDF path: {result['pdf_path']}")
            
        if result.get("error"):
            print(f"Error reported: {result['error']}")
    except Exception as e:
        print(f"CV generation error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_cv_generation()
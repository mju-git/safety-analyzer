"""Migration script to add evidence-backed fields to ingredient_safety table."""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

def migrate_ingredient_safety_table():
    """Add new columns to ingredient_safety table if they don't exist."""
    
    # Check if columns exist and add them if they don't
    migrations = [
        {
            "column": "reference_id",
            "type": "VARCHAR(255)",
            "nullable": True,
            "description": "Reference ID or document identifier (e.g., SCCS/1234/12)"
        },
        {
            "column": "document_name",
            "type": "VARCHAR(500)",
            "nullable": True,
            "description": "Document name or title (e.g., Opinion on Sodium Lauryl Sulfate)"
        },
        {
            "column": "evidence_strength",
            "type": "VARCHAR(20)",
            "nullable": True,
            "description": "Evidence strength for this specific safety profile (high/medium/low)"
        }
    ]
    
    with engine.begin() as conn:  # begin() handles transaction automatically
        for migration in migrations:
            column_name = migration["column"]
            column_type = migration["type"]
            nullable = "NULL" if migration["nullable"] else "NOT NULL"
            
            # Check if column exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='ingredient_safety' AND column_name=:column_name
            """)
            
            result = conn.execute(check_query, {"column_name": column_name})
            exists = result.fetchone() is not None
            
            if not exists:
                print(f"➕ Adding column: {column_name} ({migration['description']})")
                alter_query = text(f"""
                    ALTER TABLE ingredient_safety 
                    ADD COLUMN {column_name} {column_type} {nullable}
                """)
                conn.execute(alter_query)
                print(f"✅ Added column: {column_name}")
            else:
                print(f"⏭️  Column {column_name} already exists, skipping")
        
        print("\n✨ Migration completed!")


if __name__ == "__main__":
    print("🔄 Migrating ingredient_safety table to add evidence-backed fields...\n")
    
    try:
        migrate_ingredient_safety_table()
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        raise

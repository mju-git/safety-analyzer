"""Migration script to add new columns to ingredients table."""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

def migrate_ingredients_table():
    """Add new columns to ingredients table if they don't exist."""
    
    # Check if columns exist and add them if they don't
    migrations = [
        {
            "column": "aliases",
            "type": "JSON",
            "nullable": True
        },
        {
            "column": "confidence",
            "type": "VARCHAR(20)",
            "nullable": True
        },
        {
            "column": "sources",
            "type": "JSON",
            "nullable": True
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
                WHERE table_name='ingredients' AND column_name=:column_name
            """)
            
            result = conn.execute(check_query, {"column_name": column_name})
            exists = result.fetchone() is not None
            
            if not exists:
                print(f"➕ Adding column: {column_name}")
                alter_query = text(f"""
                    ALTER TABLE ingredients 
                    ADD COLUMN {column_name} {column_type} {nullable}
                """)
                conn.execute(alter_query)
                print(f"✅ Added column: {column_name}")
            else:
                print(f"⏭️  Column {column_name} already exists, skipping")
        
        print("\n✨ Migration completed!")


if __name__ == "__main__":
    print("🔄 Migrating ingredients table to add new columns...\n")
    
    try:
        migrate_ingredients_table()
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        raise

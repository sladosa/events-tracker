"""
Supabase Client Module
Handles all Supabase database operations with backup functionality
"""
from supabase import create_client, Client
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime
import json


class SupabaseManager:
    """Manage Supabase operations with backup and rollback capabilities."""
    
    def __init__(self, url: str, key: str):
        """Initialize Supabase client."""
        self.url = url
        self.key = key
        self.client: Client = create_client(url, key)
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test Supabase connection.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Try to query a system table
            result = self.client.table('areas').select('count', count='exact').execute()
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def execute_sql(self, sql: str) -> Tuple[bool, str]:
        """
        Execute SQL statements via Supabase API.
        
        Note: Supabase Python client doesn't directly support raw SQL execution.
        This would typically be done via:
        1. Supabase SQL Editor (Dashboard)
        2. PostgreSQL connection using psycopg2
        3. Supabase Edge Functions
        
        For now, this returns instructions.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        message = """
SQL execution via Python client is not directly supported.
Please execute the SQL using one of these methods:

1. Supabase Dashboard SQL Editor:
   - Go to your project dashboard
   - Click "SQL Editor" in the sidebar
   - Paste the generated SQL
   - Click "Run"

2. Using psycopg2 (direct PostgreSQL connection):
   - Get connection string from Supabase Dashboard → Settings → Database
   - Use psycopg2.connect() to execute SQL directly

3. Save SQL to file and apply manually
        """
        return False, message
    
    def backup_metadata(self, user_id: str) -> Dict:
        """
        Create backup of current metadata structure.
        
        Args:
            user_id: UUID of the user whose data to backup
        
        Returns:
            Dict containing all metadata
        """
        try:
            backup = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'areas': [],
                'categories': [],
                'attributes': []
            }
            
            # Backup areas
            areas = self.client.table('areas').select('*').eq('user_id', user_id).execute()
            backup['areas'] = areas.data
            
            # Backup categories (for user's areas)
            area_ids = [a['id'] for a in areas.data]
            if area_ids:
                categories = self.client.table('categories').select('*').in_('area_id', area_ids).execute()
                backup['categories'] = categories.data
                
                # Backup attributes (for user's categories)
                cat_ids = [c['id'] for c in categories.data]
                if cat_ids:
                    attributes = self.client.table('attribute_definitions').select('*').in_('category_id', cat_ids).execute()
                    backup['attributes'] = attributes.data
            
            return backup
            
        except Exception as e:
            raise Exception(f"Backup failed: {str(e)}")
    
    def detect_changes(self, current_backup: Dict, new_areas: List, 
                      new_categories: List, new_attributes: List) -> Dict:
        """
        Detect what will be added, updated, or deleted.
        
        Returns:
            Dict with changes categorized by operation type
        """
        changes = {
            'areas': {'add': [], 'update': [], 'delete': []},
            'categories': {'add': [], 'update': [], 'delete': []},
            'attributes': {'add': [], 'update': [], 'delete': []}
        }
        
        # Convert backup to dicts keyed by UUID
        current_areas = {a['id']: a for a in current_backup.get('areas', [])}
        current_categories = {c['id']: c for c in current_backup.get('categories', [])}
        current_attributes = {a['id']: a for a in current_backup.get('attributes', [])}
        
        # Detect area changes
        new_area_ids = set()
        for area in new_areas:
            new_area_ids.add(area.uuid)
            if area.uuid in current_areas:
                # Check if updated
                current = current_areas[area.uuid]
                if (current['name'] != area.name or 
                    current.get('icon') != area.icon or
                    current.get('color') != area.color):
                    changes['areas']['update'].append(area.name)
            else:
                changes['areas']['add'].append(area.name)
        
        # Detect deleted areas
        for area_id, area in current_areas.items():
            if area_id not in new_area_ids:
                changes['areas']['delete'].append(area['name'])
        
        # Detect category changes
        new_cat_ids = set()
        for cat in new_categories:
            new_cat_ids.add(cat.uuid)
            if cat.uuid in current_categories:
                current = current_categories[cat.uuid]
                if current['name'] != cat.name:
                    changes['categories']['update'].append(cat.name)
            else:
                changes['categories']['add'].append(cat.name)
        
        # Detect deleted categories
        for cat_id, cat in current_categories.items():
            if cat_id not in new_cat_ids:
                changes['categories']['delete'].append(cat['name'])
        
        # Detect attribute changes
        new_attr_ids = set()
        for attr in new_attributes:
            new_attr_ids.add(attr.uuid)
            if attr.uuid in current_attributes:
                current = current_attributes[attr.uuid]
                if current['name'] != attr.name or current['data_type'] != attr.data_type:
                    changes['attributes']['update'].append(attr.name)
            else:
                changes['attributes']['add'].append(attr.name)
        
        # Detect deleted attributes
        for attr_id, attr in current_attributes.items():
            if attr_id not in new_attr_ids:
                changes['attributes']['delete'].append(attr['name'])
        
        return changes
    
    def count_affected_events(self, deleted_category_ids: List[str]) -> int:
        """
        Count how many events will be deleted if categories are removed.
        
        Args:
            deleted_category_ids: List of category UUIDs to be deleted
        
        Returns:
            Number of events that will be cascade deleted
        """
        if not deleted_category_ids:
            return 0
        
        try:
            result = self.client.table('events').select(
                'id', count='exact'
            ).in_('category_id', deleted_category_ids).execute()
            
            return result.count or 0
        except Exception:
            return 0
    
    def apply_changes(self, user_id: str, areas: List, categories: List, 
                     attributes: List) -> Tuple[bool, str]:
        """
        Apply metadata changes to Supabase.
        Uses UPSERT for merge behavior.
        
        Args:
            user_id: UUID of the user
            areas: List of Area objects
            categories: List of Category objects
            attributes: List of Attribute objects
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Upsert areas
            area_records = []
            for area in areas:
                area_records.append({
                    'id': area.uuid,
                    'user_id': user_id,
                    'name': area.name,
                    'icon': area.icon,
                    'color': area.color,
                    'sort_order': area.sort_order,
                    'description': area.description
                })
            
            if area_records:
                self.client.table('areas').upsert(area_records).execute()
            
            # Upsert categories
            cat_records = []
            for cat in categories:
                cat_records.append({
                    'id': cat.uuid,
                    'area_id': cat.area_uuid,
                    'parent_category_id': cat.parent_uuid,
                    'name': cat.name,
                    'description': cat.description,
                    'level': cat.level,
                    'sort_order': cat.sort_order
                })
            
            if cat_records:
                self.client.table('categories').upsert(cat_records).execute()
            
            # Upsert attributes
            attr_records = []
            for attr in attributes:
                attr_records.append({
                    'id': attr.uuid,
                    'category_id': attr.category_uuid,
                    'name': attr.name,
                    'data_type': attr.data_type,
                    'unit': attr.unit,
                    'is_required': attr.is_required,
                    'default_value': attr.default_value,
                    'validation_rules': json.loads(attr.validation_rules),
                    'sort_order': attr.sort_order
                })
            
            if attr_records:
                self.client.table('attribute_definitions').upsert(attr_records).execute()
            
            return True, "Changes applied successfully"
            
        except Exception as e:
            return False, f"Failed to apply changes: {str(e)}"
    
    def delete_removed_items(self, current_backup: Dict, new_areas: List,
                           new_categories: List, new_attributes: List) -> Tuple[bool, str]:
        """
        Delete items that were removed in the new Excel.
        CASCADE will handle dependent records.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get UUIDs from new data
            new_area_ids = {a.uuid for a in new_areas}
            new_cat_ids = {c.uuid for c in new_categories}
            new_attr_ids = {a.uuid for a in new_attributes}
            
            # Find what to delete
            areas_to_delete = [
                a['id'] for a in current_backup.get('areas', [])
                if a['id'] not in new_area_ids
            ]
            
            cats_to_delete = [
                c['id'] for c in current_backup.get('categories', [])
                if c['id'] not in new_cat_ids
            ]
            
            attrs_to_delete = [
                a['id'] for a in current_backup.get('attributes', [])
                if a['id'] not in new_attr_ids
            ]
            
            # Delete in correct order (attributes, categories, areas)
            if attrs_to_delete:
                self.client.table('attribute_definitions').delete().in_('id', attrs_to_delete).execute()
            
            if cats_to_delete:
                self.client.table('categories').delete().in_('id', cats_to_delete).execute()
            
            if areas_to_delete:
                self.client.table('areas').delete().in_('id', areas_to_delete).execute()
            
            deleted_count = len(areas_to_delete) + len(cats_to_delete) + len(attrs_to_delete)
            return True, f"Deleted {deleted_count} items"
            
        except Exception as e:
            return False, f"Failed to delete items: {str(e)}"

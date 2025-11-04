"""
Reverse Engineering Module - FIXED VERSION
Converts Supabase database structure back to Excel template
"""

import pandas as pd
import io
from supabase import Client
from typing import Tuple
from pathlib import Path
from datetime import datetime

class ReverseEngineer:
    """Export Supabase metadata structure to Excel template."""

    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    def export_to_bytes(self, user_id: str) -> Tuple[bool, bytes, str]:
        """
        Export user's metadata structure to Excel bytes (for download).

        Args:
            user_id: UUID of the user whose structure to export

        Returns:
            Tuple of (success: bool, excel_bytes: bytes, message: str)
        """
        try:
            # Fetch all metadata for the user
            areas_data = self._fetch_areas(user_id)
            categories_data = self._fetch_categories(user_id)
            attributes_data = self._fetch_attributes(user_id)

            # Convert to DataFrames
            df_areas = pd.DataFrame(areas_data) if areas_data else pd.DataFrame(
                columns=['uuid', 'name', 'icon', 'color', 'sort_order', 'description']
            )

            df_categories = pd.DataFrame(categories_data) if categories_data else pd.DataFrame(
                columns=['uuid', 'area_uuid', 'parent_uuid', 'name', 'description', 'level', 'sort_order']
            )

            df_attributes = pd.DataFrame(attributes_data) if attributes_data else pd.DataFrame(
                columns=['uuid', 'category_uuid', 'name', 'data_type', 'unit',
                        'is_required', 'default_value', 'validation_rules', 'sort_order']
            )

            # Rename columns to match template format
            df_areas = df_areas.rename(columns={'id': 'uuid'})
            df_categories = df_categories.rename(columns={
                'id': 'uuid',
                'area_id': 'area_uuid',
                'parent_category_id': 'parent_uuid'
            })
            df_attributes = df_attributes.rename(columns={
                'id': 'uuid',
                'category_id': 'category_uuid'
            })

            # Select only template columns
            df_areas = df_areas[['uuid', 'name', 'icon', 'color', 'sort_order', 'description']]
            df_categories = df_categories[['uuid', 'area_uuid', 'parent_uuid', 'name',
                                          'description', 'level', 'sort_order']]
            df_attributes = df_attributes[['uuid', 'category_uuid', 'name', 'data_type',
                                          'unit', 'is_required', 'default_value',
                                          'validation_rules', 'sort_order']]

            # Convert validation_rules back to JSON string
            if not df_attributes.empty:
                df_attributes['validation_rules'] = df_attributes['validation_rules'].apply(
                    lambda x: str(x) if pd.notna(x) else '{}'
                )

            # Create Excel in memory (bytes)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_areas.to_excel(writer, sheet_name='Areas', index=False)
                df_categories.to_excel(writer, sheet_name='Categories', index=False)
                df_attributes.to_excel(writer, sheet_name='Attributes', index=False)

            excel_bytes = output.getvalue()

            counts = {
                'areas': len(df_areas),
                'categories': len(df_categories),
                'attributes': len(df_attributes)
            }

            message = (
                f"Exported successfully:\n"
                f" - {counts['areas']} Areas\n"
                f" - {counts['categories']} Categories\n"
                f" - {counts['attributes']} Attributes"
            )

            return True, excel_bytes, message

        except Exception as e:
            return False, b'', f"Export failed: {str(e)}"

    def export_to_excel(self, user_id: str, output_path: str) -> Tuple[bool, str]:
        """
        Export user's metadata structure to Excel file.

        Args:
            user_id: UUID of the user whose structure to export
            output_path: Path where to save the Excel file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Fetch all metadata for the user
            areas_data = self._fetch_areas(user_id)
            categories_data = self._fetch_categories(user_id)
            attributes_data = self._fetch_attributes(user_id)

            # Convert to DataFrames
            df_areas = pd.DataFrame(areas_data) if areas_data else pd.DataFrame(
                columns=['uuid', 'name', 'icon', 'color', 'sort_order', 'description']
            )

            df_categories = pd.DataFrame(categories_data) if categories_data else pd.DataFrame(
                columns=['uuid', 'area_uuid', 'parent_uuid', 'name', 'description', 'level', 'sort_order']
            )

            df_attributes = pd.DataFrame(attributes_data) if attributes_data else pd.DataFrame(
                columns=['uuid', 'category_uuid', 'name', 'data_type', 'unit',
                        'is_required', 'default_value', 'validation_rules', 'sort_order']
            )

            # Rename columns to match template format
            df_areas = df_areas.rename(columns={'id': 'uuid'})
            df_categories = df_categories.rename(columns={
                'id': 'uuid',
                'area_id': 'area_uuid',
                'parent_category_id': 'parent_uuid'
            })
            df_attributes = df_attributes.rename(columns={
                'id': 'uuid',
                'category_id': 'category_uuid'
            })

            # Select only template columns
            df_areas = df_areas[['uuid', 'name', 'icon', 'color', 'sort_order', 'description']]
            df_categories = df_categories[['uuid', 'area_uuid', 'parent_uuid', 'name',
                                          'description', 'level', 'sort_order']]
            df_attributes = df_attributes[['uuid', 'category_uuid', 'name', 'data_type',
                                          'unit', 'is_required', 'default_value',
                                          'validation_rules', 'sort_order']]

            # Convert validation_rules back to JSON string
            if not df_attributes.empty:
                df_attributes['validation_rules'] = df_attributes['validation_rules'].apply(
                    lambda x: str(x) if pd.notna(x) else '{}'
                )

            # Save to Excel
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df_areas.to_excel(writer, sheet_name='Areas', index=False)
                df_categories.to_excel(writer, sheet_name='Categories', index=False)
                df_attributes.to_excel(writer, sheet_name='Attributes', index=False)

            counts = {
                'areas': len(df_areas),
                'categories': len(df_categories),
                'attributes': len(df_attributes)
            }

            message = (
                f"Exported successfully:\n"
                f" - {counts['areas']} Areas\n"
                f" - {counts['categories']} Categories\n"
                f" - {counts['attributes']} Attributes"
            )

            return True, message

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def _fetch_areas(self, user_id: str) -> list:
        """Fetch all areas for a user."""
        try:
            result = self.client.table('areas').select('*').eq(
                'user_id', user_id
            ).order('sort_order').execute()
            return result.data
        except Exception as e:
            print(f"Warning: Failed to fetch areas: {e}")
            return []

    def _fetch_categories(self, user_id: str) -> list:
        """Fetch all categories for a user's areas."""
        try:
            # First get area IDs
            areas = self._fetch_areas(user_id)
            area_ids = [a['id'] for a in areas]

            if not area_ids:
                return []

            # Fetch categories for these areas
            result = self.client.table('categories').select('*').in_(
                'area_id', area_ids
            ).order('level').order('sort_order').execute()
            return result.data
        except Exception as e:
            print(f"Warning: Failed to fetch categories: {e}")
            return []

    def _fetch_attributes(self, user_id: str) -> list:
        """Fetch all attributes for a user's categories."""
        try:
            # First get category IDs
            categories = self._fetch_categories(user_id)
            cat_ids = [c['id'] for c in categories]

            if not cat_ids:
                return []

            # Fetch attributes for these categories
            result = self.client.table('attribute_definitions').select('*').in_(
                'category_id', cat_ids
            ).order('sort_order').execute()
            return result.data
        except Exception as e:
            print(f"Warning: Failed to fetch attributes: {e}")
            return []

    def create_backup_filename(self, user_id: str) -> str:
        """
        Generate timestamped backup filename.

        Args:
            user_id: UUID of the user

        Returns:
            Filename string
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        user_short = user_id[:8]  # First 8 chars of UUID
        return f"backup_{user_short}_{timestamp}.xlsx"

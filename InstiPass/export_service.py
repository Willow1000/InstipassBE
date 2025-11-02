import pandas as pd
from django.db import models
from django.http import HttpResponse
from django.core.serializers import serialize
from django.utils import timezone
import json
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime

class ExportService:
    
    @classmethod
    def export_data(cls, model, columns, filters, export_format, user):
        """Main export method"""
        try:
            # Apply filters
            queryset = cls._apply_filters(model, filters)
            
            # Get total count before selecting columns
            total_count = queryset.count()
            
            if total_count > 100000:  # Safety limit
                raise ValueError("Too many records to export. Please apply more filters.")
            
            # Select only specified columns
            if columns:
                # Handle related field selections
                actual_columns = []
                for col in columns:
                    if '__' in col:  # Related field
                        actual_columns.append(col)
                    else:
                        actual_columns.append(col)
                
                queryset = queryset.values(*actual_columns)
            else:
                # Export all fields by default
                queryset = queryset.values()
            
            # Convert to DataFrame for easier handling
            data_list = list(queryset)
            if not data_list:
                raise ValueError("No data found matching your criteria.")
            
            df = pd.DataFrame(data_list)
            
            # Process related fields and format data
            df = cls._process_dataframe(df, model, columns)
            
            # Generate export file
            response = cls._generate_export_file(df, export_format, model.__name__)
            
            return response, total_count
            
        except Exception as e:
            raise e
    
    @classmethod
    def _apply_filters(cls, model, filters):
        """Apply dynamic filters to queryset"""
        queryset = model.objects.all()
        
        for field_name, filter_value in filters.items():
            if not filter_value or field_name in ['table', 'columns', 'format']:
                continue
                
            # Handle range filters (for dates, numbers, etc.)
            if field_name.endswith('_range') and isinstance(filter_value, dict):
                real_field = field_name.replace('_range', '')
                field = cls._get_model_field(model, real_field)
                
                if field:
                    # Handle min value
                    if 'min' in filter_value and filter_value['min']:
                        try:
                            if isinstance(field, (models.DateField, models.DateTimeField)):
                                # Parse date string
                                date_val = cls._parse_date(filter_value['min'])
                                if date_val:
                                    # For datetime fields, set time to start of day for min filter
                                    if isinstance(field, models.DateTimeField):
                                        date_val = date_val.replace(hour=0, minute=0, second=0, microsecond=0)
                                        # Make timezone aware if using timezone-aware datetime fields
                                        try:
                                            if timezone.is_naive(date_val) and getattr(model._meta.get_field(real_field), 'auto_now', False) or \
                                               getattr(model._meta.get_field(real_field), 'auto_now_add', False):
                                                date_val = timezone.make_aware(date_val)
                                        except AttributeError:
                                            pass
                                    queryset = queryset.filter(**{f'{real_field}__gte': date_val})
                            else:
                                # For numeric fields
                                queryset = queryset.filter(**{f'{real_field}__gte': filter_value['min']})
                        except (ValueError, TypeError) as e:
                            print(f"Error parsing min filter for {real_field}: {e}")
                            continue
                    
                    # Handle max value
                    if 'max' in filter_value and filter_value['max']:
                        try:
                            if isinstance(field, (models.DateField, models.DateTimeField)):
                                # Parse date string
                                date_val = cls._parse_date(filter_value['max'])
                                if date_val:
                                    # For datetime fields, set time to end of day for max filter
                                    if isinstance(field, models.DateTimeField):
                                        date_val = date_val.replace(hour=23, minute=59, second=59, microsecond=999999)
                                        # Make timezone aware if using timezone-aware datetime fields
                                        try:
                                            if timezone.is_naive(date_val) and getattr(model._meta.get_field(real_field), 'auto_now', False) or \
                                               getattr(model._meta.get_field(real_field), 'auto_now_add', False):
                                                date_val = timezone.make_aware(date_val)
                                        except AttributeError:
                                            pass
                                    queryset = queryset.filter(**{f'{real_field}__lte': date_val})
                            else:
                                # For numeric fields
                                queryset = queryset.filter(**{f'{real_field}__lte': filter_value['max']})
                        except (ValueError, TypeError) as e:
                            print(f"Error parsing max filter for {real_field}: {e}")
                            continue
                continue
                
            # Handle contains filters for text fields
            if field_name.endswith('__contains'):
                real_field = field_name.replace('__contains', '')
                field = cls._get_model_field(model, real_field)
                if field and isinstance(field, (models.CharField, models.TextField)):
                    if filter_value:  # Only apply if value is not empty
                        queryset = queryset.filter(**{f'{real_field}__icontains': filter_value})
                continue
            
            # Handle regular field filtering
            field = cls._get_model_field(model, field_name)
            if not field or not filter_value:
                continue
            
            # Handle different filter types based on field type
            if isinstance(field, (models.CharField, models.TextField)):
                if isinstance(filter_value, list):
                    if filter_value:  # Only apply if list is not empty
                        queryset = queryset.filter(**{f'{field_name}__in': filter_value})
                else:
                    if filter_value:  # Only apply if value is not empty
                        queryset = queryset.filter(**{f'{field_name}__icontains': filter_value})
            
            elif isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
                try:
                    # Convert to appropriate numeric type
                    if isinstance(field, models.IntegerField):
                        filter_value = int(filter_value)
                    elif isinstance(field, models.FloatField):
                        filter_value = float(filter_value)
                    elif isinstance(field, models.DecimalField):
                        filter_value = float(filter_value)  # Will be converted properly by Django
                    queryset = queryset.filter(**{field_name: filter_value})
                except (ValueError, TypeError):
                    continue  # Skip invalid numeric values
            
            elif isinstance(field, (models.DateField, models.DateTimeField)):
                try:
                    date_val = cls._parse_date(filter_value)
                    if date_val:
                        # Make timezone aware if needed
                        if isinstance(field, models.DateTimeField):
                            try:
                                if timezone.is_naive(date_val) and getattr(field, 'auto_now', False) or \
                                   getattr(field, 'auto_now_add', False):
                                    date_val = timezone.make_aware(date_val)
                            except AttributeError:
                                pass
                        queryset = queryset.filter(**{field_name: date_val})
                except (ValueError, TypeError):
                    continue
            
            elif isinstance(field, models.BooleanField):
                # Handle various boolean representations
                if str(filter_value).lower() in ['true', '1', 'yes', 'on']:
                    queryset = queryset.filter(**{field_name: True})
                elif str(filter_value).lower() in ['false', '0', 'no', 'off']:
                    queryset = queryset.filter(**{field_name: False})
            
            elif field.is_relation:
                try:
                    # Convert to integer for foreign key relations
                    filter_value = int(filter_value)
                    queryset = queryset.filter(**{field_name: filter_value})
                except (ValueError, TypeError):
                    continue
        
        return queryset

    @classmethod
    def _parse_date(cls, date_string):
        """Parse date string to datetime object"""
        if not date_string:
            return None
        
        try:
            # Handle yyyy/mm/dd format (from your date range input)
            if isinstance(date_string, str) and len(date_string) == 10 and date_string.count('/') == 2:
                # Try yyyy/mm/dd format first
                try:
                    return datetime.strptime(date_string, '%Y/%m/%d')
                except ValueError:
                    # Try dd/mm/yyyy format as fallback
                    try:
                        return datetime.strptime(date_string, '%d/%m/%Y')
                    except ValueError:
                        # Try mm/dd/yyyy format as last resort
                        return datetime.strptime(date_string, '%m/%d/%Y')
            
            # Handle YYYY-MM-DD format (ISO date format)
            if isinstance(date_string, str) and len(date_string) == 10 and date_string.count('-') == 2:
                return datetime.strptime(date_string, '%Y-%m-%d')
            
            # Handle full ISO datetime format (like your database format: 2025-06-08T14:55:33.352Z)
            if isinstance(date_string, str) and 'T' in date_string:
                # Remove timezone info and microseconds for parsing
                clean_date = date_string.replace('Z', '').split('T')[0]
                return datetime.strptime(clean_date, '%Y-%m-%d')
            
            # Handle datetime strings with time but no 'T' separator
            if isinstance(date_string, str) and len(date_string) > 10 and ' ' in date_string:
                # Try to parse datetime with various formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M']:
                    try:
                        return datetime.strptime(date_string, fmt)
                    except ValueError:
                        continue
                # If time parsing fails, just parse the date part
                date_part = date_string.split(' ')[0]
                return cls._parse_date(date_part)
            
            # Try parsing as timestamp if it's a number
            if isinstance(date_string, (int, float)):
                return datetime.fromtimestamp(date_string)
            
            return None
            
        except (ValueError, TypeError) as e:
            print(f"Error parsing date '{date_string}': {e}")
            return None
    
    @classmethod
    def _get_model_field(cls, model, field_name):
        try:
            # Handle related field lookups
            if '__' in field_name:
                base_field = field_name.split('__')[0]
                return model._meta.get_field(base_field)
            return model._meta.get_field(field_name)
        except Exception as e:
            print(f"an error occured {e}")
            return None
    
    @classmethod
    def _process_dataframe(cls, df, model, columns):
        """Convert foreign keys to readable values and format data"""
        for column in df.columns:
            # Handle related fields
            if '__' in column:
                base_field, related_field = column.split('__', 1)
                try:
                    field = model._meta.get_field(base_field)
                    if field.is_relation:
                        # This is already handled by the values() query
                        continue
                except:
                    pass
            
            # Format specific field types
            if 'date' in column.lower() or 'timestamp' in column.lower() or 'created' in column.lower() or 'updated' in column.lower():
                # Handle datetime formatting
                df[column] = pd.to_datetime(df[column], errors='coerce')
                # Format datetime to readable string
                df[column] = df[column].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
            
            # Convert None to empty string
            df[column] = df[column].fillna('')
            
            # Truncate very long text to prevent export issues
            df[column] = df[column].astype(str).apply(lambda x: x[:100] + '...' if len(x) > 100 else x)
        
        return df
    
    @classmethod
    def _generate_export_file(cls, df, export_format, table_name):
        """Generate file based on format"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{table_name}_{timestamp}"
        
        if export_format == 'csv':
            return cls._export_csv(df, filename)
        elif export_format == 'excel':
            return cls._export_excel(df, filename)
        elif export_format == 'json':
            return cls._export_json(df, filename)
        elif export_format == 'pdf':
            return cls._export_pdf(df, filename)
        else:
            raise ValueError(f"Unsupported format: {export_format}")
    
    @classmethod
    def _export_csv(cls, df, filename):
        """Export data as CSV file"""
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename={filename}.csv'
        return response
    
    @classmethod
    def _export_excel(cls, df, filename):
        """Export data as Excel file"""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Export')
            workbook = writer.book
            worksheet = writer.sheets['Export']
            
            # Add auto-filter
            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            
            # Adjust column widths
            for i, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, min(max_len, 50))
            
            # Add header formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={filename}.xlsx'
        return response
    
    @classmethod
    def _export_json(cls, df, filename):
        """Export data as JSON file"""
        # Convert DataFrame to dict and then to JSON for better formatting
        data_dict = {
            'export_info': {
                'filename': filename,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_records': len(df)
            },
            'data': df.to_dict('records')
        }
        
        json_data = json.dumps(data_dict, indent=2, ensure_ascii=False, default=str)
        response = HttpResponse(json_data, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename={filename}.json'
        return response
    
    @classmethod
    def _export_pdf(cls, df, filename):
        """Export data as PDF file"""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={filename}.pdf'
        
        doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=20, rightMargin=20, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title and metadata
        title = Paragraph(f"Data Export: {filename.replace('_', ' ').title()}", styles['Title'])
        elements.append(title)
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph(f"Total records: {len(df)}", styles['Normal']))
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # Convert DataFrame to table
        if len(df) > 0:
            # Prepare table data - limit columns to fit page width
            max_cols = 6  # Adjust based on your needs
            if len(df.columns) > max_cols:
                display_df = df.iloc[:, :max_cols]
                truncated_note = f"Note: Showing first {max_cols} columns out of {len(df.columns)} total columns."
                elements.append(Paragraph(truncated_note, styles['Normal']))
                elements.append(Paragraph("<br/>", styles['Normal']))
            else:
                display_df = df
            
            # Prepare table data
            table_data = [display_df.columns.tolist()]  # Header
            
            # Add data rows (limit to first 50 rows for PDF readability)
            max_rows = 50
            for i, (_, row) in enumerate(display_df.iterrows()):
                if i >= max_rows:
                    break
                table_data.append([str(cell)[:30] + '...' if len(str(cell)) > 30 else str(cell) for cell in row.tolist()])
            
            if len(df) > max_rows:
                elements.append(Paragraph(f"Note: Showing first {max_rows} rows out of {len(df)} total rows.", styles['Normal']))
                elements.append(Paragraph("<br/>", styles['Normal']))
            
            # Create table with improved styling
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), True)
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph("No data to display", styles['Normal']))
        
        doc.build(elements)
        return response
    
    @classmethod
    def get_model_fields(cls, model):
        """Get all fields from a model for column selection"""
        fields = []
        for field in model._meta.get_fields():
            if not field.is_relation or field.one_to_one or (field.many_to_one and hasattr(field, 'related_name')):
                field_name = field.name
                field_verbose = getattr(field, 'verbose_name', field_name)
                fields.append({
                    'name': field_name,
                    'verbose_name': field_verbose,
                    'type': field.__class__.__name__
                })
        return fields
    
    @classmethod
    def validate_export_request(cls, model, columns, filters, export_format):
        """Validate export request parameters"""
        errors = []
        
        # Validate export format
        valid_formats = ['csv', 'excel', 'json', 'pdf']
        if export_format not in valid_formats:
            errors.append(f"Invalid export format. Must be one of: {', '.join(valid_formats)}")
        
        # Validate columns exist in model
        if columns:
            model_fields = [f.name for f in model._meta.get_fields()]
            for column in columns:
                if '__' in column:  # Related field
                    base_field = column.split('__')[0]
                    if base_field not in model_fields:
                        errors.append(f"Invalid column: {column}")
                elif column not in model_fields:
                    errors.append(f"Invalid column: {column}")
        
        # Validate filter fields exist
        for field_name in filters.keys():
            if field_name in ['table', 'columns', 'format']:
                continue
            real_field = field_name.replace('_range', '').replace('__contains', '')
            if not cls._get_model_field(model, real_field):
                errors.append(f"Invalid filter field: {field_name}")
        
        return errors
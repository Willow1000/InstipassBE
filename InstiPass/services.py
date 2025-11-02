# services.py
from django.apps import apps
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
import uuid

class SchemaService:
    FIELD_TYPE_MAPPING = {
        models.CharField: 'text',
        models.TextField: 'text',
        models.EmailField: 'email',
        models.IntegerField: 'number',
        models.FloatField: 'number',
        models.DecimalField: 'number',
        models.BooleanField: 'boolean',
        models.DateField: 'date',
        models.DateTimeField: 'datetime',
        models.ImageField: 'image',
        models.FileField: 'file',
        models.URLField: 'url',
        models.GenericIPAddressField: 'ip',
        models.UUIDField: 'uuid',
    }
    
    # Define which models should be available for export
    EXPORTABLE_MODELS = [
        'User', 'SignupTracker', 'InstitutionSignupToken', 'InstitutionRegistrationToken',
        'ContactUsTracker', 'DemoBookingTracker', 'Institution', 'InstitutionSettings',
        'InstitutionToken', 'RegistrationTracker', 'Notifications', 
        'Payment', 'NewsLetter', 'ContactUs', 'DemoBooking', 'Issue', 'Testimonial',
        'APIAccessLog', 'IdprogressLog', 'AdminActionsLog', 'BlackListLog', 'DemoLogs',
        'Student', 'SubmissionTracker','ExportLog','AdminNotification',"BannedIP","InstitutionMagicLinkToken","PaymentProofVerification","TransactionsLog","PaymentReceiptDownloadToken","Deficits","InvoiceDownloadToken","LoginTracker"
    ]
    
    @classmethod
    def get_table_schema(cls, table_name):
        """Get schema for a specific table"""
        try:
            model = cls._get_model_by_name(table_name)
            if not model:
                return None
            
            columns = []
            for field in model._meta.get_fields():
                # Skip many-to-many and reverse relations
                if field.auto_created or (field.is_relation and field.many_to_many):
                    continue
                    
                field_info = {
                    'name': field.name,
                    'verbose_name': getattr(field, 'verbose_name', field.name.title().replace('_', ' ')),
                    'type': cls._get_field_type(field),
                    'max_length': getattr(field, 'max_length', None),
                    'choices': cls._get_field_choices(field),
                    'related_model': field.related_model.__name__ if field.is_relation else None,
                    'help_text': getattr(field, 'help_text', ''),
                    'is_relation': field.is_relation,
                }
                
                # Add field-specific attributes
                if hasattr(field, 'validators'):
                    for validator in field.validators:
                        if isinstance(validator, MinValueValidator):
                            field_info['min_value'] = validator.limit_value
                        elif isinstance(validator, MaxValueValidator):
                            field_info['max_value'] = validator.limit_value
                
                columns.append(field_info)
            
            return {
                'table': table_name,
                'verbose_name': model._meta.verbose_name or table_name,
                'columns': columns,
                'total_records': model.objects.count()
            }
        except Exception as e:
            print(f"Error getting schema for {table_name}: {e}")
            return None
    
    @classmethod
    def get_available_tables(cls):
        """Get list of all available tables/models"""
        tables = []
        for model in apps.get_models():
            if model.__name__ in cls.EXPORTABLE_MODELS:
                tables.append({
                    'name': model.__name__,
                    'verbose_name': model._meta.verbose_name or model.__name__,
                    'app_label': model._meta.app_label,
                    'total_records': model.objects.count()
                })
        return sorted(tables, key=lambda x: x['verbose_name'])
    
    @classmethod
    def _get_model_by_name(cls, model_name):
        for model in apps.get_models():
            if model.__name__ == model_name:
                return model
        return None
    
    @classmethod
    def _get_field_type(cls, field):
        for field_class, type_name in cls.FIELD_TYPE_MAPPING.items():
            if isinstance(field, field_class):
                return type_name
        
        # Handle ForeignKey and OneToOne fields
        if field.is_relation:
            if isinstance(field, models.ForeignKey):
                return 'foreign_key'
            elif isinstance(field, models.OneToOneField):
                return 'one_to_one'
        
        return 'text'
    
    @classmethod
    def _get_field_choices(cls, field):
        if hasattr(field, 'choices') and field.choices:
            return [{'value': choice[0], 'label': choice[1]} for choice in field.choices]
        return None
    
    @classmethod
    def get_model_instance(cls, model_name):
        """Get model class by name"""
        return cls._get_model_by_name(model_name)
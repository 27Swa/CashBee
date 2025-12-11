from django.utils.html import format_html
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse
from .models import User, Family


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_members_count', 'created_at')
    search_fields = ('name',)
    readonly_fields = ['created_at', 'updated_at']
    
    def get_members_count(self, obj):
        return obj.get_members_count()
    get_members_count.short_description = 'Members'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'phone_number', 'name', 'national_id', 'role', 'family', 'is_active')
    list_filter = ['role', 'is_active', 'is_staff', 'family']
    search_fields = ['phone_number', 'national_id', 'first_name', 'last_name', 'username']
    ordering = ['phone_number']
    
    fieldsets = (
        (None, {'fields': ('username', 'phone_number', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'national_id', 'email', 'date_of_birth')}),
        ('Family & Role', {'fields': ('role', 'family')}),
        ('Security', {'fields': ('failed_attempts', 'lock_time')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'national_id', 'password1', 'password2', 'role'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override to use custom manager for creating users"""
        if not change:  # Creating new user
            # Password is already set by the form, so we just save
            obj.save(skip_validation=True)
        else:  # Updating existing user
            obj.save(skip_validation=True)
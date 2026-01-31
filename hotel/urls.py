# -*- coding: utf-8 -*-
"""
URLs pour l'application hotel
Configuration de toutes les routes de l'application
"""

from django.urls import path
from . import views
from . import views_billing
from . import views_inventory

urlpatterns = [
    # Authentification
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards par rôle
    path('dashboard/', views.dashboard, name='dashboard'),  # Ancien dashboard (garde pour compatibilité)
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/employe/', views.dashboard_employe, name='dashboard_employe'),
    path('dashboard/client/', views.dashboard_client, name='dashboard_client'),
    
    # Pages client spécifiques
    path('client/dashboard/', views.dashboard_client, name='client_dashboard'),
    path('client/chambres/', views.chambres_client, name='client_chambres'),
    path('client/reservation/', views.reservation_client, name='client_reservation'),
    path('client/reservations/<int:pk>/details/', views.reservation_details_api, name='reservation_details_api'),
    path('client/reservations/<int:pk>/modify/', views.reservation_modify_api, name='reservation_modify_api'),
    path('client/reservations/<int:pk>/cancel/', views.reservation_cancel_api, name='reservation_cancel_api'),
    path('client/contact/', views.contact_client, name='client_contact'),
    path('client/profile/', views.profile_client, name='client_profile'),
    path('client/settings/', views.settings_client, name='client_settings'),
    path('client/test-reservation/', views.create_test_reservation, name='create_test_reservation'),
    
    # API pour vérification de disponibilité
    path('api/check-disponibilite/', views.check_disponibilite_api, name='check_disponibilite_api'),
    # API pour réservation
    path('api/creer-reservation/', views.creer_reservation_api, name='creer_reservation_api'),
    # API pour chambres disponibles
    path('api/chambres-disponibles/', views.chambres_disponibles_api, name='chambres_disponibles_api'),
    
    # Gestion des clients
    path('clients/', views.client_list, name='client_list'),
    path('clients/new/', views.client_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.client_update, name='client_update'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('clients/<int:pk>/password/', views.client_change_password, name='client_change_password'),
    
    # Gestion des chambres
    path('chambres/', views.chambre_list, name='chambre_list'),
    path('chambres/new/', views.chambre_create, name='chambre_create'),
    path('chambres/<int:pk>/edit/', views.chambre_update, name='chambre_update'),
    path('chambres/<int:pk>/delete/', views.chambre_delete, name='chambre_delete'),
    
    # Gestion des réservations
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/new/', views.reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('reservations/<int:pk>/edit/', views.reservation_update, name='reservation_update'),
    path('reservations/<int:pk>/delete/', views.reservation_delete, name='reservation_delete'),
    
    # API Chatbot
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    # Inscription client
    path('signup/', views.client_signup, name='client_signup'),
    # Création employé (admin only)
    path('employees/new/', views.create_employee, name='create_employee'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('employees/<int:pk>/promote/', views.employee_promote, name='employee_promote'),
    path('employees/<int:pk>/salary/', views.employee_change_salary, name='employee_change_salary'),
    path('employees/<int:pk>/role/', views.employee_change_role, name='employee_change_role'),
    path('employees/<int:pk>/terminate/', views.employee_terminate, name='employee_terminate'),
    path('employees/<int:pk>/history/', views.employee_history, name='employee_history'),
    
    # Gestion de la facturation (nouveau système comptable)
    path('billing/', views_billing.billing_dashboard, name='billing_list'),
    path('billing/invoice/<int:invoice_id>/', views_billing.invoice_detail, name='billing_invoice'),
    path('billing/invoice/<int:invoice_id>/pdf/', views_billing.invoice_pdf, name='billing_invoice_pdf'),
    path('billing/payslip/<int:payslip_id>/', views_billing.payslip_detail, name='billing_payslip'),
    path('billing/charge/<int:charge_id>/', views_billing.charge_detail, name='billing_charge'),
    path('billing/mark-paid/', views_billing.mark_as_paid, name='billing_mark_paid'),
    path('billing/export/', views_billing.export_csv, name='billing_export'),
    path('billing/generate-report/', views_billing.generate_monthly_report, name='billing_generate_report'),
    path('billing/create-payslip/', views_billing.create_payslip, name='billing_create_payslip'),
    path('billing/api/stats/', views_billing.dashboard_stats_api, name='billing_stats_api'),
    path('billing/create-inventory-charge/', views_billing.create_inventory_charge, name='billing_create_inventory_charge'),
    
    # Anciennes URLs (compatibilité)
    path('billing/old/', views.billing_list, name='billing_list_old'),
    path('billing/invoice/<int:pk>/', views.billing_invoice, name='billing_invoice_old'),
    path('billing/<int:invoice_id>/record-payment/', views.record_payment, name='record_payment'),
    
    # Autres pages de gestion
    path('calendar/', views.calendar_view, name='calendar'),
    
    # Gestion de l'inventaire (nouvelles vues améliorées)
    path('inventory/', views_inventory.InventoryListView.as_view(), name='inventory_list'),
    path('inventory/new/', views_inventory.InventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views_inventory.InventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/edit/', views_inventory.InventoryUpdateView.as_view(), name='inventory_edit'),
    path('inventory/<int:pk>/delete/', views_inventory.InventoryDeleteView.as_view(), name='inventory_delete'),
    path('inventory/movement/', views_inventory.inventory_movement, name='inventory_movement'),
    path('inventory/export/', views_inventory.inventory_export, name='inventory_export'),
    path('inventory/api/stats/', views_inventory.inventory_stats_api, name='inventory_stats_api'),
    
    # Anciennes URLs inventory (compatibilité)
    path('inventory/old/', views.inventory_list, name='inventory_list_old'),
    path('inventory/create/', views.inventory_create, name='inventory_create_old'),
    path('inventory/<int:pk>/update/', views.inventory_update, name='inventory_update_old'),
    path('inventory/<int:pk>/movement/', views.inventory_movement, name='inventory_movement_old'),
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/new/', views.maintenance_create, name='maintenance_create'),
    path('maintenance/<int:pk>/', views.maintenance_detail, name='maintenance_detail'),
    path('maintenance/<int:pk>/edit/', views.maintenance_edit, name='maintenance_edit'),
    path('maintenance/<int:pk>/complete/', views.maintenance_complete, name='maintenance_complete'),
    path('reports/', views.reports_view, name='reports'),
    
    # Administration des messages de contact
    path('management/messages/', views.admin_messages_contact, name='admin_messages_contact'),
    path('management/messages/<int:pk>/', views.admin_message_detail, name='admin_message_detail'),
    path('management/messages/<int:pk>/update-statut/', views.admin_message_update_statut, name='admin_message_update_statut'),
    
    # Gestion des notifications admin
    path('management/notifications/', views.admin_notifications, name='admin_notifications'),
    path('management/notifications/<int:notification_id>/lue/', views.notification_marquer_lue, name='notification_marquer_lue'),
    path('management/notifications/<int:notification_id>/traitee/', views.notification_marquer_traitee, name='notification_marquer_traitee'),
    path('management/notifications/marquer-toutes-lues/', views.notification_marquer_toutes_lues, name='notification_marquer_toutes_lues'),
    
    # Réponses aux messages clients
    path('management/notifications/contact-message/<int:notification_id>/details/', views_billing.get_contact_message_details, name='get_contact_message_details'),
    path('notifications/reply-to-client/', views_billing.reply_to_client_message, name='reply_to_client_message'),
    
    # Vues améliorées maintenance
    path('maintenance/improved/', views.maintenance_list_improved, name='maintenance_list_improved'),
    path('maintenance/<int:maintenance_id>/update-status/', views.maintenance_update_status, name='maintenance_update_status'),
    path('maintenance/<int:maintenance_id>/link-inventory/', views.maintenance_link_inventory, name='maintenance_link_inventory'),
    
    # Gestion de l'agent IA (admin uniquement)
    path('management/agent-ia/', views.agent_ia_dashboard, name='agent_ia_dashboard'),
    path('management/agent-ia/toggle/', views.agent_ia_toggle_activation, name='agent_ia_toggle_activation'),
    path('management/agent-ia/update-config/', views.agent_ia_update_config, name='agent_ia_update_config'),
    path('management/agent-ia/interactions/', views.agent_ia_view_interactions, name='agent_ia_view_interactions'),
]

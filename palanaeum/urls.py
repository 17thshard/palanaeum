# coding=utf-8
from django.conf import settings as project_settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.urls import path, re_path, reverse_lazy
from django.views.i18n import JavaScriptCatalog

import palanaeum.staff_views
from palanaeum import views, settings, staff_views, audio_fine_upload_views, \
    admin_views
from palanaeum.api.urls import api_router
from palanaeum.configuration import get_config
from palanaeum.feeds import RecentEntriesFeed, EventEntriesFeed
from palanaeum.sitemaps import EventSitemap

js_info_dict = {
    'packages': ('palanaeum',),
}

password_change_kwargs = {
    'template_name': 'palanaeum/auth/password_change.html',
    'success_url': reverse_lazy('auth_password_change_done')
}

password_reset_kwargs = {
    'template_name': 'palanaeum/auth/password_reset.html',
    'email_template_name': 'palanaeum/email/password_reset.html',
    'subject_template_name': 'palanaeum/email/password_reset_subject.html',
    'success_url': reverse_lazy('auth_password_reset_done'),
    'extra_context': {'site_name': get_config('page_title')}
}

password_reset_done_kwargs = {
    'template_name': 'palanaeum/auth/password_reset_done.html'
}

password_reset_confirm_kwargs = {
    'template_name': 'palanaeum/auth/password_reset_complete.html',
    'success_url': reverse_lazy('auth_password_reset_complete')
}

urlpatterns = [
    path('', views.index, name='index'),
    path('jsi18n/', JavaScriptCatalog.as_view(**js_info_dict), name='jsi18n'),
    path('events/', views.events, name='events_list'),
    path('events/create/', staff_views.edit_event, name='create_event'),
    path('events/<int:event_id>/', views.event_no_slug, name='view_event_no_title'),
    re_path(r'^events/(?P<event_id>\d+)-([^/]+)/$', views.view_event, name='view_event'),
    path('events/<int:event_id>/feed/', views.event_feed_no_slug, name='event_feed_no_title'),
    re_path(r'^events/(?P<event_id>\d+)-([^/]+)?/feed/$', EventEntriesFeed(), name='event_feed'),
    path('events/<int:event_id>/edit/', staff_views.edit_event, name='edit_event'),
    path('events/<int:event_id>/delete/', staff_views.remove_event, name='remove_event'),
    path('events/<int:event_id>/source/choose_type/', palanaeum.staff_views.choose_source_type, name='event_choose_source_type'),
    path('events/<int:event_id>/source/upload/audio/',
        palanaeum.staff_views.upload_audio_page,
        name='event_upload_audio'),
    path('events/<int:event_id>/source/upload/images/',
        palanaeum.staff_views.upload_images_page,
        name='event_upload_images'),
    path('events/<int:event_id>/sort_entries/', staff_views.sort_entries_page, name="sort_entries"),
    path('events/<int:event_id>/sort_entries/snippets/', staff_views.reorder_entries_by_snippets, name="sort_entries_by_snippets"),
    path('events/<int:event_id>/sort_entries/creation_date/', staff_views.reorder_entries_by_creation_date, name="sort_entries_by_creation_date"),
    path('events/<int:event_id>/sort_entries/date/', staff_views.reorder_entries_by_assigned_date, name="sort_entries_by_assigned_date"),
    path('save_entries_order/', staff_views.save_entries_order, name="save_entries_order"),

    path('events/<int:event_id>/add_entry/', staff_views.edit_entry, name='event_add_entry'),

    path('recent/', views.recent_entries, name="recent_entries"),
    path('recent/feed/', RecentEntriesFeed(), name="recent_entries_feed"),

    path('entry/<int:entry_id>/', views.view_entry, name="view_entry"),
    path('entry/<int:entry_id>/edit/', staff_views.edit_entry, name='edit_entry'),
    path('entry/<int:entry_id>/delete/', staff_views.remove_entry, name='remove_entry'),
    path('entry/<int:entry_id>/history/', staff_views.show_entry_history, name='entry_history'),
    path('entry/<int:entry_id>/approve/', staff_views.approve_entry, name='approve_entry'),
    path('entry/<int:entry_id>/reject/', staff_views.reject_entry, name='reject_entry'),
    path('entry/<int:entry_id>/move/', staff_views.move_entry, name='move_entry'),
    path('entry/save/', staff_views.save_entry, name='save_entry'),

    path('source/audio/<int:source_id>/edit/', staff_views.edit_audio_source, name='edit_audio_source'),
    path('source/audio/rename/', staff_views.rename_audio_source, name='rename_audio_source'),
    path('source/audio/<int:file_id>/delete/', staff_views.remove_audio_file, name='remove_audio_file'),
    path('source/audio/<int:source_id>/mute/', staff_views.mute_snippet, name='mute_snippet'),
    path('source/get_url_text/', staff_views.get_url_text, name='get_url_text'),

    path('snippets/create/', staff_views.get_new_snippet_id, name='get_new_snippet_id'),
    path('snippets/edit/', staff_views.update_snippets, name='update_snippets'),
    path('snippets/delete/', staff_views.delete_snippet, name='delete_snippet'),
    path('snippet/<int:snippet_id>/edit_entry/', staff_views.edit_snippet_entry, name='edit_snippet_entry'),
    path('snippet/<int:snippet_id>/create_entry/', staff_views.create_entry_for_snippet, name='create_entry_for_snippet'),
    path('snippet/<int:snippet_id>/unlink/', staff_views.unlink_snippet, name='unlink_snippet'),

    path('hide_show_resource/', staff_views.hide_show_resource, name='hide_show_resource'),

    path('source/upload/image/', staff_views.upload_images_endpoint, name='image_source_upload'),
    # path('source/upload/finished/', audio_fine_upload_views.upload_finished, name='audio_source_upload_finished'),
    re_path(r'^source/upload(?:/(?P<qquuid>\S+))?', audio_fine_upload_views.UploadView.as_view(),
        name='audio_source_upload'),
    path('source/image/<int:source_id>/assign_entry/', staff_views.edit_image_source_entry, name="edit_image_entry"),
    path('source/image/<int:source_id>/create_entry/', staff_views.create_entry_for_image_source, name='create_entry_for_image_source'),
    path('source/image/<int:source_id>/delete/', staff_views.remove_image_source, name='remove_image_source'),
    path('source/image/<int:source_id>/rename/', staff_views.rename_image_source, name='rename_image_source'),

    re_path(r'^source/(?P<source_type>audio|image)/(?P<pk>\d+)/approve/', staff_views.approve_source, name='approve_source'),
    re_path(r'^source/(?P<source_type>audio|image)/(?P<pk>\d+)/reject/', staff_views.reject_source, name='reject_source'),

    path('get_tags/', views.get_tags, name="get_tags"),
    path('tags/', views.tags_list, name="tags_list"),
    path('adv_search/', views.adv_search, name="advanced_search"),
    path('todo/', views.untranscribed_snippets, name="todo_snippets"),

    path('collections/create/', views.edit_collection, name="collection_create"),
    path('collections/ajax/get/', views.get_collection_list_json, name="collections_list_json"),
    path('collections/ajax/edit/', views.switch_entry_in_collection, name="collections_add_rem_entry"),
    path('collections/ajax/create/', views.ajax_add_collection, name="collections_ajax_add_collection"),
    path('collections/<int:collection_id>/', views.show_collection, name="collection_details"),
    path('collections/<int:collection_id>/edit/', views.edit_collection, name="collection_edit"),
    path('collections/<int:collection_id>/delete/', views.delete_collection, name="collection_delete"),
    path('collections/', views.show_collection_list, name="collections_list"),

    path('admin/', admin_views.index, name="admin_index"),
    path('admin/config/', admin_views.config, name="admin_config"),
    path('admin/config/reset_favicons/', admin_views.reset_favicons, name="admin_config_reset_favicons"),
    path('admin/users/', admin_views.users_list, name="admin_users"),
    path('admin/users/edit/', admin_views.set_user_state, name="admin_users_edit"),
    path('admin/realted_sites/', admin_views.related_sites_list, name="admin_related_sites"),
    path('admin/realted_sites/<int:site_id>/', admin_views.related_site_edit, name="admin_related_site_edit"),
    path('admin/realted_sites/edit/', admin_views.related_site_edit, name="admin_related_site_new"),
    path('admin/realted_sites/<int:site_id>/delete/', admin_views.related_site_delete, name="admin_related_site_delete"),

    path('staff/', staff_views.staff_cp, name="staff_index"),
    path('staff/suggestions/', staff_views.staff_cp_suggestions, name='staff_suggestions'),

    path('auth/login/', auth_views.LoginView.as_view(template_name='palanaeum/auth/login.html'), name='auth_login'),
    path('auth/logout/', auth_views.LogoutView.as_view(next_page='/'), name='auth_logout'),
    path('auth/password_change/', auth_views.PasswordChangeView.as_view(**password_change_kwargs), name='auth_password_change'),
    path('auth/password_change/done/', views.password_change_complete, name='auth_password_change_done'),
    path('auth/password_reset/', auth_views.PasswordResetView.as_view(**password_reset_kwargs), name='auth_password_reset'),
    path('auth/password_reset/done/', auth_views.PasswordResetCompleteView.as_view(**password_reset_done_kwargs),
        name='auth_password_reset_done'),
    re_path(r'^auth/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(**password_reset_confirm_kwargs), name='auth_password_reset_confirm'),
    path('auth/reset/done/', views.password_reset_complete, name='auth_password_reset_complete'),
    path('auth/register/', views.register_user, name='auth_register'),
    path('auth/profile/', views.user_settings, name='auth_settings'),

    path('sitemap.xml', sitemap, {'sitemaps': {'events': EventSitemap}}, name='django.contrib.sitemaps.views.sitemap'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include(api_router.urls))


] + static(project_settings.MEDIA_URL, document_root=project_settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

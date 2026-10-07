"""Generated from the mounted public OpenAPI document. Do not edit."""
from __future__ import annotations
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Literal, Never, NotRequired, Required, TypedDict, cast
from urllib.parse import quote
import httpx
from .management import ApiResult, ManagementOptions, ManagementTransport, MultipartInput, QueryValue, WriteOptions

AccountDomainPatch = TypedDict('AccountDomainPatch', {'application_grants': NotRequired['list[DomainGrant] | None'], 'auto_join_enabled': NotRequired['bool | None']})

AccountPolicyPatch = TypedDict('AccountPolicyPatch', {'invitations_enabled': NotRequired['bool'], 'remember_device_days': NotRequired['int']})

AccountPolicyResource = TypedDict('AccountPolicyResource', {'invitations_enabled': Required['bool'], 'remember_device_days': Required['int']})

ActList = TypedDict('ActList', {'items': Required['list[ActResource]'], 'page': Required['Page']})

ActResource = TypedDict('ActResource', {'account_deleted_at': Required['str | None'], 'application_client_id': Required['str | None'], 'application_id': Required['str | None'], 'channel': Required['str'], 'decided_at': Required['str'], 'decision': Required["Literal['accepted'] | Literal['declined']"], 'document_url': Required['str'], 'id': Required['str'], 'key': Required['str'], 'label': Required['str'], 'language': Required['str'], 'organization_id': Required['str | None'], 'revoked_at': Required['str | None'], 'revoked_channel': Required['str | None'], 'scope': Required["Literal['application'] | Literal['organization']"], 'subject_digest': Required['str | None'], 'subject_id': Required['str | None'], 'version': Required['int']})

AdministrativePolicy = TypedDict('AdministrativePolicy', {'label': Required['str | None'], 'min_acr': Required["Literal['1'] | Literal['mfa'] | Literal['mfa-strong'] | Literal['phr']"], 'role': NotRequired["Literal['org:admin']"]})

AdministrativePolicyPatch = TypedDict('AdministrativePolicyPatch', {'label': NotRequired['str | None'], 'min_acr': NotRequired["Literal['1'] | Literal['mfa'] | Literal['mfa-strong'] | Literal['phr']"]})

AgentInstructionsResource = TypedDict('AgentInstructionsResource', {'active_entry_methods': Required['list[str]'], 'client_id': Required['str'], 'framework': Required['str'], 'frameworks': Required['list[FrameworkResource]'], 'instructions': Required['str'], 'issuer': Required['str'], 'redirect_uris': Required['list[str]'], 'sdk_package': Required['str']})

AppleConfig = TypedDict('AppleConfig', {'key_id': Required['str'], 'team_id': Required['str']})

Application = TypedDict('Application', {'active': Required['bool'], 'client_id': Required['str'], 'client_type': Required["Literal['m2m'] | Literal['spa'] | Literal['bff'] | Literal['native']"], 'console_family': Required['bool'], 'created_at': Required['str'], 'display_name': Required['str'], 'id': Required['str'], 'identity_mode': Required["Literal['individual'] | Literal['organizations']"], 'invitable': Required['bool'], 'invitations_enabled': Required['bool'], 'updated_at': Required['str']})

ApplicationCreate = TypedDict('ApplicationCreate', {'client_id': NotRequired['str | None'], 'client_type': NotRequired["Literal['m2m'] | Literal['spa'] | Literal['bff'] | Literal['native']"], 'display_name': Required['str'], 'identity_mode': NotRequired["Literal['individual'] | Literal['organizations']"], 'public': NotRequired['bool'], 'redirect_uris': NotRequired['list[str]']})

ApplicationList = TypedDict('ApplicationList', {'items': Required['list[Application]'], 'page': Required['Page']})

ApplicationPatch = TypedDict('ApplicationPatch', {'active': NotRequired['bool'], 'display_name': NotRequired['str'], 'identity_mode': NotRequired["Literal['individual'] | Literal['organizations']"]})

AssetResource = TypedDict('AssetResource', {'digest': Required['str'], 'url': Required['str']})

AssignedAccess = TypedDict('AssignedAccess', {'access': Required["Literal['individual'] | Literal['all'] | Literal['explicit'] | Literal['none']"], 'application_id': Required['str'], 'organization_id': Required['str | None'], 'role_ids': Required['list[str]'], 'user_id': Required['str']})

AuditEventList = TypedDict('AuditEventList', {'items': Required['list[AuditEventResource]'], 'page': Required['Page']})

AuditEventResource = TypedDict('AuditEventResource', {'actor_id': Required['str | None'], 'actor_kind': Required['str'], 'actor_tenant': Required['str'], 'capability': Required['str'], 'channel': Required['str'], 'client_id': Required['str | None'], 'id': Required['str'], 'method': Required['str'], 'occurred_at': Required['str'], 'organization_id': Required['str | None'], 'path_template': Required['str | None'], 'resource': Required['str | None'], 'status_code': Required['int | None']})

AuthenticationPatch = TypedDict('AuthenticationPatch', {'backchannel_logout_uri': NotRequired['str | None'], 'entry_methods': NotRequired['list[str]'], 'min_acr': NotRequired["Literal['1'] | Literal['mfa'] | Literal['mfa-strong'] | Literal['phr']"], 'org_api_enabled': NotRequired['bool'], 'post_logout_redirect_uris': NotRequired['list[str]'], 'redirect_uris': NotRequired['list[str]'], 'require_pkce': NotRequired['bool']})

AuthenticationResource = TypedDict('AuthenticationResource', {'application_id': Required['str'], 'backchannel_logout_uri': Required['str | None'], 'console_family': Required['bool'], 'entry_methods': Required['list[str]'], 'min_acr': Required["Literal['1'] | Literal['mfa'] | Literal['mfa-strong'] | Literal['phr']"], 'org_api_enabled': Required['bool'], 'post_logout_redirect_uris': Required['list[str]'], 'redirect_uris': Required['list[str]'], 'require_pkce': Required['bool']})

BodyAssetsAccountApiV1BrandingAssetsPost = TypedDict('BodyAssetsAccountApiV1BrandingAssetsPost', {'logo': Required['str']})

BodyAssetsApplicationApiV1ApplicationsApplicationIdBrandingAssetsPost = TypedDict('BodyAssetsApplicationApiV1ApplicationsApplicationIdBrandingAssetsPost', {'logo': Required['str']})

BoundGrant = TypedDict('BoundGrant', {'role_ids': Required['list[str]']})

BrandingResource = TypedDict('BrandingResource', {'available_languages': NotRequired['list[str] | None'], 'configured': Required['Theme | None'], 'contrast': Required['Contrast'], 'effective': Required['Theme'], 'language': NotRequired['str | None'], 'seal': NotRequired['SealState | None'], 'sources': Required['ThemeSources']})

ChannelList = TypedDict('ChannelList', {'items': Required['list[ChannelResource]'], 'page': Required['Page']})

ChannelPatch = TypedDict('ChannelPatch', {'config': NotRequired['EmailConfig | SmsConfig | WhatsappConfig'], 'form': NotRequired["Literal['channel'] | Literal['assignment']"], 'monthly_limit': NotRequired['int | None'], 'sender_domain': NotRequired['str | None']})

ChannelResource = TypedDict('ChannelResource', {'check': Required['CheckState | None'], 'configured': Required['Configured | None'], 'effective': Required['Effective'], 'sources': Required['Sources'], 'type': Required["Literal['email'] | Literal['sms'] | Literal['whatsapp']"]})

CheckState = TypedDict('CheckState', {'checked_at': Required['str | None'], 'last_answer': Required["Literal['present'] | Literal['absent'] | Literal['unknown'] | None"], 'state': Required["Literal['idle'] | Literal['checking']"]})

ClaimsPut = TypedDict('ClaimsPut', {'claims': Required['dict[str, str]']})

ClaimsResource = TypedDict('ClaimsResource', {'application_id': Required['str'], 'claims': Required['dict[str, str]']})

Configured = TypedDict('Configured', {'blocked_this_period': Required['int'], 'config': Required['PublicConfig'], 'created_at': Required['str'], 'exempt_this_period': Required['int'], 'form': Required["Literal['channel'] | Literal['assignment']"], 'id': Required['str'], 'monthly_limit': Required['int | None'], 'recovery_dependents': Required['int | None'], 'sender_domain': Required['str | None'], 'sent_this_period': Required['int'], 'transport_status': Required["Literal['ok'] | Literal['error'] | Literal['failing'] | None"], 'transport_status_at': Required['str | None'], 'transport_status_error': Required["Literal['provider_payment_required'] | Literal['delivery_failed'] | None"], 'updated_at': Required['str'], 'verification': Required['StwrdIdpAdminApiChannelsVerification | None']})

ConfirmationErrorResponse = TypedDict('ConfirmationErrorResponse', {'confirmation_token': Required['str'], 'consequence': Required['Consequence'], 'error': Required['Error']})

ConnectionCreate = TypedDict('ConnectionCreate', {'client_id': NotRequired['str | None'], 'client_secret': NotRequired['str'], 'config': Required['EmptyConfig | AppleConfig | MicrosoftConfig | OidcConfig | SamlConfig'], 'display_name': NotRequired['str | None'], 'enabled': NotRequired['bool'], 'provider': Required["Literal['google'] | Literal['apple'] | Literal['microsoft'] | Literal['github'] | Literal['oidc'] | Literal['saml']"], 'provider_key': Required['str']})

ConnectionList = TypedDict('ConnectionList', {'items': Required['list[ConnectionResource]'], 'page': Required['Page']})

ConnectionPatch = TypedDict('ConnectionPatch', {'clear_client_secret': NotRequired['bool'], 'client_id': NotRequired['str | None'], 'client_secret': NotRequired['str'], 'config': NotRequired['EmptyConfig | AppleConfig | MicrosoftConfig | OidcConfig | SamlConfig'], 'display_name': NotRequired['str | None'], 'enabled': NotRequired['bool'], 'provider': NotRequired["Literal['google'] | Literal['apple'] | Literal['microsoft'] | Literal['github'] | Literal['oidc'] | Literal['saml']"]})

ConnectionResource = TypedDict('ConnectionResource', {'client_id': Required['str | None'], 'config': Required['EmptyConfig | AppleConfig | MicrosoftConfig | OidcConfig | SamlConfig'], 'created_at': Required['str'], 'display_name': Required['str | None'], 'enabled': Required['bool'], 'has_client_secret': Required['bool'], 'id': Required['str'], 'organization_id': Required['str | None'], 'protocol': Required["Literal['oidc'] | Literal['oauth2'] | Literal['saml']"], 'provider': Required["Literal['google'] | Literal['apple'] | Literal['microsoft'] | Literal['github'] | Literal['oidc'] | Literal['saml']"], 'provider_key': Required['str'], 'redirect_uris': Required['list[str]'], 'updated_at': Required['str']})

ConsentLabelsIncompleteErrorResponse = TypedDict('ConsentLabelsIncompleteErrorResponse', {'error': Required['Error'], 'missing_languages': Required['list[str]']})

ConsentLanguageErrorResponse = TypedDict('ConsentLanguageErrorResponse', {'consent_terms': Required['list[ConsentLanguageTerm]'], 'error': Required['Error']})

ConsentLanguageTerm = TypedDict('ConsentLanguageTerm', {'consent_id': Required['str'], 'key': Required['str'], 'label': Required['str'], 'missing_languages': Required['list[str]']})

Consequence = TypedDict('Consequence', {'display_name': Required['str'], 'effects': Required['list[Effect]'], 'resource_id': Required['str'], 'resource_type': Required['str']})

Contact = TypedDict('Contact', {'email': Required['str'], 'pending_email': Required['str | None'], 'pending_expires_at': Required['str | None'], 'url': Required['str | None'], 'verified_at': Required['str | None']})

ContactSources = TypedDict('ContactSources', {'contact': Required['Source']})

ContextActor = TypedDict('ContextActor', {'id': Required['str'], 'type': Required["Literal['operator'] | Literal['tenant_admin'] | Literal['m2m'] | Literal['monitor'] | Literal['org_admin'] | Literal['user']"]})

ContextResource = TypedDict('ContextResource', {'account': Required['MinimalResource'], 'actor': Required['ContextActor'], 'application': Required['MinimalResource | None'], 'capabilities': Required['list[str]'], 'organization': Required['MinimalResource | None']})

Contrast = TypedDict('Contrast', {'fill_dark': Required['str'], 'fill_degenerate_dark': Required['bool'], 'fill_degenerate_light': Required['bool'], 'fill_light': Required['str'], 'fill_ratio_dark': Required['float'], 'fill_ratio_light': Required['float'], 'ring_dark': Required['str'], 'ring_light': Required['str'], 'text_dark': Required['str'], 'text_light': Required['str']})

CopyTarget = TypedDict('CopyTarget', {'env_file': Required['str | None'], 'key': Required['str'], 'label': Required['str'], 'var_name': Required['str']})

DelegatedDomainPatch = TypedDict('DelegatedDomainPatch', {'auto_join_enabled': NotRequired['bool | None'], 'grant': NotRequired['BoundGrant | None']})

DeliveryList = TypedDict('DeliveryList', {'items': Required['list[DeliveryResource]'], 'page': Required['Page']})

DeliveryResource = TypedDict('DeliveryResource', {'application_display_name': Required['str | None'], 'application_id': Required['str'], 'attempts': Required['int'], 'created_at': Required['str'], 'delivered_at': Required['str | None'], 'endpoint_id': Required['str'], 'event_id': Required['str'], 'id': Required['str'], 'last_error_code': Required['str | None'], 'next_attempt_at': Required['str | None'], 'redacted_at': Required['str | None'], 'retryable': Required['bool'], 'status': Required["Literal['pending'] | Literal['delivered'] | Literal['exhausted']"], 'type': Required['str']})

DestinationChange = TypedDict('DestinationChange', {'url': Required['str']})

DnsCheckResource = TypedDict('DnsCheckResource', {'checked_at': Required['str | None'], 'last_answer': Required['str | None'], 'state': Required["Literal['idle'] | Literal['checking']"]})

DomainCreate = TypedDict('DomainCreate', {'domain': Required['str']})

DomainGrant = TypedDict('DomainGrant', {'application_id': Required['str'], 'role_ids': Required['list[str]']})

DomainList = TypedDict('DomainList', {'items': Required['list[DomainResource]'], 'page': Required['Page']})

DomainResource = TypedDict('DomainResource', {'active': NotRequired['bool | None'], 'application_grants': NotRequired['list[DomainGrant] | None'], 'application_id': Required['str | None'], 'auto_join_enabled': NotRequired['bool | None'], 'canonical_host': NotRequired['str | None'], 'check': Required['DnsCheckResource'], 'checked_at': Required['str | None'], 'created_at': Required['str'], 'domain': Required['str'], 'edge': NotRequired['str | None'], 'id': Required['str'], 'organization_id': Required['str | None'], 'purpose': Required["Literal['account_name'] | Literal['login'] | Literal['organization']"], 'superseded_host': NotRequired['str | None'], 'verification': Required['StwrdIdpAdminApiDomainsVerification'], 'verification_status': Required['str'], 'verified_at': Required['str | None']})

Effect = TypedDict('Effect', {'code': Required['str'], 'count': Required['int']})

Effective = TypedDict('Effective', {'form': Required["Literal['channel'] | Literal['assignment'] | None"], 'offered': Required['bool'], 'rests_on_system': Required['bool'], 'sender': Required['str | None'], 'sender_honored': Required['bool | None'], 'templates': Required['dict[str, JsonValue] | None'], 'transport_status': Required["Literal['ok'] | Literal['error'] | Literal['failing'] | None"]})

EffectiveContact = TypedDict('EffectiveContact', {'email': Required['str | None'], 'url': Required['str | None']})

EmailConfig = TypedDict('EmailConfig', {'host': NotRequired['str'], 'password': NotRequired['str'], 'port': NotRequired['int'], 'sender': NotRequired['str | None'], 'username': NotRequired['str']})

EmailIdentity = TypedDict('EmailIdentity', {'sender': NotRequired['str | None'], 'sender_domain': NotRequired['None']})

EmailTestResult = TypedDict('EmailTestResult', {'blocked_at': Required["Literal['tenant'] | Literal['organization'] | Literal['client'] | Literal['system'] | None"], 'branch': Required["Literal['email']"], 'channel': Required['ChannelResource'], 'charged': Required['bool'], 'error': Required["Literal['delivery_failed'] | None"], 'exempt': Required['bool'], 'flow_id': Required['None'], 'sent': Required['bool'], 'verified': Required['None']})

type Empty = dict[str, Any]

type EmptyConfig = dict[str, Any]

type EmptyRequest = dict[str, Any]

EnableApplication = TypedDict('EnableApplication', {'member_access': Required["Literal['all'] | Literal['selected']"]})

EnabledApplication = TypedDict('EnabledApplication', {'active': Required['bool'], 'application_id': Required['str'], 'created_at': Required['str'], 'display_name': Required['str'], 'invitable': Required['bool'], 'invitations_enabled': Required['bool'], 'member_access': Required["Literal['all'] | Literal['selected']"], 'organization_id': Required['str'], 'updated_at': Required['str']})

EnabledApplicationList = TypedDict('EnabledApplicationList', {'items': Required['list[EnabledApplication]'], 'page': Required['Page']})

EndpointCreate = TypedDict('EndpointCreate', {'application_id': Required['str'], 'display_name': NotRequired['str | None'], 'enabled': NotRequired['bool'], 'subscriptions': Required['list[str]'], 'url': Required['str']})

EndpointList = TypedDict('EndpointList', {'items': Required['list[EndpointResource]'], 'page': Required['Page']})

EndpointPatch = TypedDict('EndpointPatch', {'display_name': NotRequired['str | None'], 'enabled': NotRequired['bool'], 'subscriptions': NotRequired['list[str]']})

EndpointResource = TypedDict('EndpointResource', {'application_id': Required['str'], 'created_at': Required['str'], 'display_name': Required['str | None'], 'enabled': Required['bool'], 'id': Required['str'], 'previous_secret_expires_at': Required['str | None'], 'secret_configured': Required['bool'], 'subscriptions': Required['list[str]'], 'updated_at': Required['str'], 'url': Required['str | None']})

EntryPatch = TypedDict('EntryPatch', {'default_organization_id': NotRequired['str | None'], 'default_role_ids': NotRequired['list[str]'], 'invitations_enabled': NotRequired['bool'], 'recovery_methods': NotRequired['list[str]'], 'require_email_verified': NotRequired['bool'], 'require_recovery_email': NotRequired['bool'], 'signup_mode': NotRequired["Literal['closed'] | Literal['open'] | Literal['waitlist']"], 'signup_rules': NotRequired['dict[str, list[str]]']})

EntryResource = TypedDict('EntryResource', {'default_organization_id': Required['str | None'], 'default_role_ids': Required['list[str]'], 'entry_immutable': Required['bool'], 'id': Required['str'], 'invitations_enabled': Required['bool'], 'recovery_methods': Required['dict[str, Any]'], 'require_email_verified': Required['bool'], 'require_recovery_email': Required['bool'], 'requirements': Required['list[dict[str, Any]]'], 'signup_mode': Required["Literal['closed'] | Literal['open'] | Literal['waitlist']"], 'signup_rules': Required['dict[str, list[str]]']})

Error = TypedDict('Error', {'code': Required['str'], 'details': Required['list[FieldError]'], 'message': Required['str'], 'request_id': Required['str']})

ErrorResponse = TypedDict('ErrorResponse', {'error': Required['Error']})

EventTypeList = TypedDict('EventTypeList', {'items': Required['list[EventTypeResource]'], 'page': Required['Page']})

EventTypeResource = TypedDict('EventTypeResource', {'data_schema': Required['dict[str, Any]'], 'description_key': Required['str'], 'type': Required['str']})

FieldError = TypedDict('FieldError', {'code': Required['str'], 'field': Required['str'], 'message': Required['str']})

FrameworkResource = TypedDict('FrameworkResource', {'key': Required['str'], 'label': Required['str']})

HttpvalidationError = TypedDict('HttpvalidationError', {'detail': NotRequired['list[ValidationError]']})

ImpactResource = TypedDict('ImpactResource', {'users_affected': Required['int']})

InvitationCreate = TypedDict('InvitationCreate', {'application_id': Required['str'], 'email': Required['str'], 'organization_id': NotRequired['str | None'], 'role_ids': NotRequired['list[str]']})

InvitationList = TypedDict('InvitationList', {'items': Required['list[InvitationResource]'], 'page': Required['Page']})

InvitationResource = TypedDict('InvitationResource', {'accepted_at': Required['str | None'], 'application_display_name': Required['str'], 'application_id': Required['str'], 'canceled_at': Required['str | None'], 'created_at': Required['str'], 'email': Required['str'], 'expires_at': Required['str'], 'id': Required['str'], 'organization_id': Required['str | None'], 'role_ids': Required['list[str]'], 'status': Required["Literal['pending'] | Literal['accepted'] | Literal['canceled'] | Literal['expired'] | Literal['invalid']"]})

type JsonValue = Any

LanguagePatch = TypedDict('LanguagePatch', {'language': Required['str | None']})

MembershipCreate = TypedDict('MembershipCreate', {'administrator': NotRequired['bool'], 'metadata': NotRequired['dict[str, Any]'], 'user_id': Required['str']})

MembershipList = TypedDict('MembershipList', {'items': Required['list[MembershipResource]'], 'page': Required['Page']})

MembershipPatch = TypedDict('MembershipPatch', {'administrator': NotRequired['bool'], 'metadata': NotRequired['dict[str, Any]']})

MembershipResource = TypedDict('MembershipResource', {'administrator': Required['bool'], 'created_at': Required['str'], 'email': Required['str | None'], 'metadata': Required['dict[str, Any]'], 'name': Required['str | None'], 'organization_id': Required['str'], 'user_id': Required['str']})

MessageApplication = TypedDict('MessageApplication', {'display_name': Required['str | None'], 'id': Required['str']})

MessageList = TypedDict('MessageList', {'items': Required['list[MessageResource]'], 'page': Required['Page']})

MessageResource = TypedDict('MessageResource', {'application': Required['MessageApplication | None'], 'application_id': Required['str | None'], 'attempts': Required['int'], 'channel_type': Required["Literal['email'] | Literal['sms'] | Literal['whatsapp']"], 'created_at': Required['str'], 'delivered_at': Required['str | None'], 'expires_at': Required['str | None'], 'id': Required['str'], 'last_error_code': Required["Literal['expired'] | Literal['redacted'] | Literal['provider_payment_required'] | None"], 'next_attempt_at': Required['str | None'], 'organization_id': Required['str | None'], 'origin_level': Required['str'], 'recipient': Required['str | None'], 'recipient_domain': Required['str | None'], 'redacted_at': Required['str | None'], 'status': Required['str'], 'template': Required['str'], 'updated_at': Required['str']})

MfaResetResult = TypedDict('MfaResetResult', {'mfa_reset': Required['bool'], 'user_id': Required['str']})

MicrosoftConfig = TypedDict('MicrosoftConfig', {'tenant': Required['str']})

MinimalResource = TypedDict('MinimalResource', {'display_name': Required['str | None'], 'id': Required['str']})

OidcConfig = TypedDict('OidcConfig', {'issuer': Required['str']})

OrganizationCreate = TypedDict('OrganizationCreate', {'admin_user_id': NotRequired['str | None'], 'display_name': Required['str']})

OrganizationList = TypedDict('OrganizationList', {'items': Required['list[OrganizationResource]'], 'page': Required['Page']})

OrganizationPatch = TypedDict('OrganizationPatch', {'display_name': NotRequired['str']})

OrganizationResource = TypedDict('OrganizationResource', {'created_at': Required['str'], 'display_name': Required['str'], 'has_admin': Required['bool'], 'id': Required['str'], 'member_count': Required['int'], 'updated_at': Required['str']})

Page = TypedDict('Page', {'next_cursor': Required['str | None'], 'total': Required['int | None']})

PermissionList = TypedDict('PermissionList', {'items': Required['list[PermissionResource]'], 'page': Required['Page']})

PermissionResource = TypedDict('PermissionResource', {'id': Required['str'], 'key': Required['str']})

PermissionsPut = TypedDict('PermissionsPut', {'permissions': Required['list[str]']})

PermissionsResource = TypedDict('PermissionsResource', {'application_id': Required['str'], 'permissions': Required['list[str]'], 'roles_affected': Required['int']})

PhoneConfirm = TypedDict('PhoneConfirm', {'code': Required['str'], 'flow_id': Required['str'], 'phone': Required['str']})

PhoneConfirmResult = TypedDict('PhoneConfirmResult', {'blocked_at': Required['None'], 'branch': Required["Literal['phone_confirm']"], 'channel': Required['ChannelResource'], 'charged': Required['Literal[False]'], 'error': Required['None'], 'exempt': Required['Literal[False]'], 'flow_id': Required['str'], 'sent': Required['None'], 'verified': Required['Literal[True]']})

PhoneStart = TypedDict('PhoneStart', {'phone': Required['str']})

PhoneStartResult = TypedDict('PhoneStartResult', {'blocked_at': Required['None'], 'branch': Required["Literal['phone_start']"], 'channel': Required['ChannelResource'], 'charged': Required['Literal[False]'], 'error': Required["Literal['delivery_failed'] | None"], 'exempt': Required['Literal[False]'], 'flow_id': Required['str | None'], 'sent': Required['bool'], 'verified': Required['None']})

PreviewRequest = TypedDict('PreviewRequest', {'language': NotRequired['str | None'], 'overrides': NotRequired['Theme | None'], 'screen': Required['str']})

PreviewResponse = TypedDict('PreviewResponse', {'html': Required['str']})

PublicConfig = TypedDict('PublicConfig', {'account_sid': NotRequired['str | None'], 'allowed_country_prefixes': NotRequired['list[str] | None'], 'business_account_id': NotRequired['str | None'], 'from_number': NotRequired['str | None'], 'host': NotRequired['str | None'], 'phone_number_id': NotRequired['str | None'], 'port': NotRequired['int | None'], 'secrets_configured': Required['dict[str, bool]'], 'sender': NotRequired['str | None'], 'templates': NotRequired['dict[str, JsonValue] | None'], 'username': NotRequired['str | None']})

PublishForm = TypedDict('PublishForm', {'document': Required['str'], 'effective_at': NotRequired['str | None'], 'version': NotRequired['int | None']})

ReceiptPatch = TypedDict('ReceiptPatch', {'enabled': Required['bool']})

ReceiptResource = TypedDict('ReceiptResource', {'enabled': Required['bool']})

RecoveryResult = TypedDict('RecoveryResult', {'expires_in': Required['int'], 'sent': Required['bool'], 'user_id': Required['str']})

RetentionPatch = TypedDict('RetentionPatch', {'consent_retention_years': NotRequired['int'], 'litigation_hold': NotRequired['bool']})

RetentionResource = TypedDict('RetentionResource', {'consent_retention_years': Required['int'], 'litigation_hold_at': Required['str | None']})

RoleCreate = TypedDict('RoleCreate', {'key': Required['str'], 'label': NotRequired['str | None'], 'min_acr': NotRequired["Literal['1'] | Literal['mfa'] | Literal['mfa-strong'] | Literal['phr']"], 'permission_ids': NotRequired['list[str]']})

RoleList = TypedDict('RoleList', {'items': Required['list[RoleResource]'], 'page': Required['Page']})

RolePatch = TypedDict('RolePatch', {'label': NotRequired['str | None'], 'min_acr': NotRequired["Literal['1'] | Literal['mfa'] | Literal['mfa-strong'] | Literal['phr']"], 'permission_ids': NotRequired['list[str]']})

RoleResource = TypedDict('RoleResource', {'application_id': Required['str'], 'created_at': Required['str'], 'id': Required['str'], 'key': Required['str'], 'label': Required['str | None'], 'min_acr': Required["Literal['1'] | Literal['mfa'] | Literal['mfa-strong'] | Literal['phr']"], 'permission_ids': Required['list[str]'], 'updated_at': Required['str']})

RolesPut = TypedDict('RolesPut', {'role_ids': Required['list[str]']})

RotationCreate = TypedDict('RotationCreate', {'mode': NotRequired["Literal['rotate'] | Literal['cut'] | Literal['retry']"]})

SamlConfig = TypedDict('SamlConfig', {'certificate': Required['str'], 'idp_entity_id': Required['str'], 'sso_url': Required['str']})

SealPatch = TypedDict('SealPatch', {'hidden': Required['bool | None']})

SealState = TypedDict('SealState', {'declared_at': Required["Literal['product'] | Literal['account'] | Literal['application'] | Literal['organization'] | None"], 'effective_hidden': Required['bool'], 'hidden': Required['bool | None'], 'plan_default_hidden': Required['bool'], 'unlock_requires': Required['dict[str, bool]'], 'unlocked': Required['bool']})

SelfMembership = TypedDict('SelfMembership', {'active': Required['bool'], 'organization': Required['MinimalResource']})

SelfMembershipList = TypedDict('SelfMembershipList', {'items': Required['list[SelfMembership]'], 'page': Required['Page']})

SelfUserResource = TypedDict('SelfUserResource', {'avatar_url': Required['str | None'], 'display_name': Required['str | None'], 'email': Required['str | None'], 'email_verified': Required['bool'], 'id': Required['str']})

SessionList = TypedDict('SessionList', {'items': Required['list[SessionResource]'], 'page': Required['Page']})

SessionResource = TypedDict('SessionResource', {'authenticated_at': Required['str'], 'created_at': Required['str'], 'expires_at': Required['str'], 'id': Required['str'], 'last_seen_at': Required['str'], 'revoked_at': Required['str | None'], 'user_id': Required['str']})

SigningKeyList = TypedDict('SigningKeyList', {'items': Required['list[SigningKeyResource]'], 'page': Required['Page']})

SigningKeyResource = TypedDict('SigningKeyResource', {'alg': Required['str'], 'created_at': Required['str'], 'id': Required['str'], 'kid': Required['str'], 'public_jwk': Required['dict[str, JsonValue]'], 'retired_at': Required['str | None'], 'rotated_at': Required['str | None'], 'status': Required["Literal['active'] | Literal['retiring'] | Literal['retired']"]})

SmsConfig = TypedDict('SmsConfig', {'account_sid': NotRequired['str'], 'allowed_country_prefixes': NotRequired['list[str]'], 'auth_token': NotRequired['str'], 'from_number': NotRequired['str']})

Source = TypedDict('Source', {'level': Required["Literal['product'] | Literal['account'] | Literal['application'] | Literal['organization']"], 'resource_id': Required['str | None']})

Sources = TypedDict('Sources', {'identity': Required['Source | None'], 'transport': Required['Source | None']})

StepUpDescriptor = TypedDict('StepUpDescriptor', {'endpoint': Required['str'], 'factors': Required['list[str]'], 'header': Required['str'], 'ttl_s': Required['int']})

StepUpErrorResponse = TypedDict('StepUpErrorResponse', {'capability': Required['str'], 'error': Required['Error'], 'step_up': Required['StepUpDescriptor']})

StepUpRequest = TypedDict('StepUpRequest', {'backup_code': NotRequired['str | None'], 'capability': Required['str'], 'totp': NotRequired['str | None']})

SupportPatch = TypedDict('SupportPatch', {'email': NotRequired['str'], 'url': NotRequired['str | None']})

SupportResource = TypedDict('SupportResource', {'configured': Required['Contact | None'], 'effective': Required['EffectiveContact'], 'sources': Required['ContactSources']})

TermCreate = TypedDict('TermCreate', {'blocking': Required['bool'], 'key': Required['str'], 'kind': NotRequired["Literal['consent'] | Literal['declaration']"], 'labels': Required['dict[str, str]'], 'revocable': Required['bool'], 'role': NotRequired["Literal['terms'] | Literal['privacy'] | None"]})

TermList = TypedDict('TermList', {'items': Required['list[TermResource]'], 'languages': Required['list[str]'], 'page': Required['Page']})

TermMutationResponse = TypedDict('TermMutationResponse', {'application_id': Required['str | None'], 'blocking': Required['bool'], 'created_at': Required['str'], 'current_version': Required['int | None'], 'id': Required['str'], 'key': Required['str'], 'kind': Required["Literal['consent'] | Literal['declaration']"], 'labels': Required['dict[str, str]'], 'missing_languages': Required['list[str]'], 'new_version': Required['int | None'], 'on_behalf_of': Required["Literal['account'] | None"], 'organization_id': Required['str | None'], 'pending_after': Required['int'], 'retired_at': Required['str | None'], 'revocable': Required['bool'], 'role': Required["Literal['terms'] | Literal['privacy'] | None"], 'updated_at': Required['str'], 'users_affected': Required['int']})

TermPatch = TypedDict('TermPatch', {'blocking': NotRequired['bool'], 'labels': NotRequired['dict[str, str]'], 'revocable': NotRequired['bool'], 'role': NotRequired["Literal['terms'] | Literal['privacy'] | None"]})

TermResource = TypedDict('TermResource', {'application_id': Required['str | None'], 'blocking': Required['bool'], 'created_at': Required['str'], 'current_version': Required['int | None'], 'id': Required['str'], 'key': Required['str'], 'kind': Required["Literal['consent'] | Literal['declaration']"], 'labels': Required['dict[str, str]'], 'missing_languages': Required['list[str]'], 'on_behalf_of': Required["Literal['account'] | None"], 'organization_id': Required['str | None'], 'retired_at': Required['str | None'], 'revocable': Required['bool'], 'role': Required["Literal['terms'] | Literal['privacy'] | None"], 'updated_at': Required['str']})

TestLoginResource = TypedDict('TestLoginResource', {'authorize_url': Required['str'], 'expires_at': Required['str'], 'redirect_uri': Required['str']})

TestResource = TypedDict('TestResource', {'delivery_id': Required['str'], 'event_id': Required['str']})

Theme = TypedDict('Theme', {'display_name': NotRequired['str | None'], 'logo_url': NotRequired['str | None'], 'primary_color': NotRequired['str | None']})

ThemeSources = TypedDict('ThemeSources', {'display_name': Required['Source | None'], 'logo_url': Required['Source | None'], 'primary_color': Required['Source | None']})

TokensPatch = TypedDict('TokensPatch', {'access_token_ttl_s': NotRequired['int | None'], 'allowed_scopes': NotRequired['list[str]'], 'audience': NotRequired['str | None'], 'signing_alg': NotRequired["Literal['EdDSA'] | Literal['RS256']"], 'token_endpoint_auth_method': NotRequired["Literal['client_secret_basic'] | Literal['client_secret_post'] | Literal['none']"]})

TokensResource = TypedDict('TokensResource', {'access_token_ttl_s': Required['int | None'], 'allowed_scopes': Required['list[str]'], 'application_id': Required['str'], 'audience': Required['str | None'], 'authorization_endpoint': Required['str'], 'client_id': Required['str'], 'client_secret_prev_expires_at': Required['str | None'], 'client_type': Required['str'], 'issuer': Required['str'], 'jwks_uri': Required['str'], 'last_login_at': Required['str | None'], 'public': Required['bool'], 'secret_configured': Required['bool'], 'secret_rotation_overlap_hours': Required['int'], 'signing_alg': Required["Literal['EdDSA'] | Literal['RS256']"], 'token_endpoint': Required['str'], 'token_endpoint_auth_method': Required["Literal['client_secret_basic'] | Literal['client_secret_post'] | Literal['none']"]})

UserCreate = TypedDict('UserCreate', {'email': Required['str'], 'email_verified': NotRequired['Literal[False]'], 'imported_credential': NotRequired['str | None'], 'metadata': NotRequired['dict[str, Any]'], 'name': NotRequired['str | None'], 'password': NotRequired['str | None']})

UserDeletionResult = TypedDict('UserDeletionResult', {'accounts_without_owner_count': Required['int'], 'deleted': Required['bool'], 'id': Required['str'], 'organizations_without_admin_count': Required['int']})

UserList = TypedDict('UserList', {'items': Required['list[UserResource]'], 'page': Required['Page']})

UserPatch = TypedDict('UserPatch', {'email_verified': NotRequired['Literal[False]'], 'metadata': NotRequired['dict[str, Any]'], 'name': NotRequired['str | None'], 'status': NotRequired["Literal['active'] | Literal['suspended']"]})

UserResource = TypedDict('UserResource', {'created_at': Required['str'], 'email': Required['str'], 'email_verified': Required['bool'], 'id': Required['str'], 'metadata': Required['dict[str, Any]'], 'mfa_factors': Required["list[Literal['totp'] | Literal['passkey'] | Literal['phone']]"], 'name': Required['str | None'], 'processing_blocked_at': Required['str | None'], 'status': Required["Literal['pending'] | Literal['active'] | Literal['suspended']"], 'updated_at': Required['str']})

UserRevocationResult = TypedDict('UserRevocationResult', {'revoked_count': Required['int'], 'user_id': Required['str']})

ValidationError = TypedDict('ValidationError', {'ctx': NotRequired['dict[str, Any]'], 'input': NotRequired['Any'], 'loc': Required['list[str | int]'], 'msg': Required['str'], 'type': Required['str']})

VerificationQueued = TypedDict('VerificationQueued', {'status': NotRequired['str']})

VersionList = TypedDict('VersionList', {'items': Required['list[VersionResource]'], 'page': Required['Page']})

VersionResource = TypedDict('VersionResource', {'consent_id': Required['str'], 'document_digest': Required['str'], 'document_url': Required['str'], 'effective_at': Required['str | None'], 'published_at': Required['str'], 'users_affected': Required['int'], 'version': Required['int']})

WebhookRotationErrorResponse = TypedDict('WebhookRotationErrorResponse', {'error': Required['Error'], 'previous_secret_expires_at': Required['str']})

WhatsappConfig = TypedDict('WhatsappConfig', {'access_token': NotRequired['str'], 'business_account_id': NotRequired['str'], 'phone_number_id': NotRequired['str'], 'templates': NotRequired['dict[str, JsonValue] | None']})

WhatsappIdentity = TypedDict('WhatsappIdentity', {'templates': NotRequired['dict[str, JsonValue] | None']})

StwrdIdpAdminApiChannelsVerification = TypedDict('StwrdIdpAdminApiChannelsVerification', {'checked_at': Required['str | None'], 'record_name': Required['str | None'], 'record_value': Required['str | None'], 'sender_domain': Required['str | None'], 'sender_honored': Required['bool | None'], 'status': Required["Literal['unverified'] | Literal['pending'] | Literal['verified'] | Literal['failed']"], 'verified_at': Required['str | None']})

StwrdIdpAdminApiDomainsVerification = TypedDict('StwrdIdpAdminApiDomainsVerification', {'record_name': Required['str'], 'record_value': Required['str | None']})

StwrdIdpAdminApiWebhookEndpointsRotationResource = TypedDict('StwrdIdpAdminApiWebhookEndpointsRotationResource', {'copy_targets': Required['list[CopyTarget]'], 'previous_secret_expires_at': Required['str | None'], 'rotation_id': Required['str'], 'var_name': Required['str'], 'webhook_secret': Required['str']})

StwrdIdpAdminApiWebhookEndpointsSecretResource = TypedDict('StwrdIdpAdminApiWebhookEndpointsSecretResource', {'copy_targets': Required['list[CopyTarget]'], 'var_name': Required['str'], 'webhook_secret': Required['str']})

StwrdIdpAdminApplicationConfigurationRotationResource = TypedDict('StwrdIdpAdminApplicationConfigurationRotationResource', {'client_secret': Required['str'], 'client_secret_prev_expires_at': Required['str | None'], 'copy_targets': Required['list[dict[str, str | None]]'], 'rotation_id': Required['str'], 'var_name': Required['str']})

StwrdIdpAdminApplicationConfigurationSecretResource = TypedDict('StwrdIdpAdminApplicationConfigurationSecretResource', {'client_secret': Required['str'], 'copy_targets': Required['list[dict[str, str | None]]'], 'var_name': Required['str']})

ListApplicationsApiV1ApplicationsGetQuery = TypedDict('ListApplicationsApiV1ApplicationsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'client_id': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class CreateApplicationApiV1ApplicationsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

GetAgentInstructionsApiV1ApplicationsApplicationIdAgentInstructionsGetQuery = TypedDict('GetAgentInstructionsApiV1ApplicationsApplicationIdAgentInstructionsGetQuery', {'framework': NotRequired['str']})

@dataclass(frozen=True, kw_only=True)
class AssetsApplicationApiV1ApplicationsApplicationIdBrandingAssetsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListApplicationApiV1ApplicationsApplicationIdChannelsGetQuery = TypedDict('ListApplicationApiV1ApplicationsApplicationIdChannelsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None']})

@dataclass(frozen=True, kw_only=True)
class TestApplicationApiV1ApplicationsApplicationIdChannelsChannelTypeTestPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class VerifyApplicationApiV1ApplicationsApplicationIdChannelsChannelTypeVerifyPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

AppListApiV1ApplicationsApplicationIdConsentsGetQuery = TypedDict('AppListApiV1ApplicationsApplicationIdConsentsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class AppCreateApiV1ApplicationsApplicationIdConsentsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

AppVersionsApiV1ApplicationsApplicationIdConsentsConsentIdVersionsGetQuery = TypedDict('AppVersionsApiV1ApplicationsApplicationIdConsentsConsentIdVersionsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class AppPublishApiV1ApplicationsApplicationIdConsentsConsentIdVersionsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListApplicationDomainsApiV1ApplicationsApplicationIdDomainsGetQuery = TypedDict('ListApplicationDomainsApiV1ApplicationsApplicationIdDomainsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class CreateApplicationDomainApiV1ApplicationsApplicationIdDomainsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class ActivateApplicationDomainApiV1ApplicationsApplicationIdDomainsDomainIdActivatePostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class VerifyApplicationDomainApiV1ApplicationsApplicationIdDomainsDomainIdVerifyPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListPermissionsApiV1ApplicationsApplicationIdPermissionsGetQuery = TypedDict('ListPermissionsApiV1ApplicationsApplicationIdPermissionsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

ListRolesApiV1ApplicationsApplicationIdRolesGetQuery = TypedDict('ListRolesApiV1ApplicationsApplicationIdRolesGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class CreateRoleApiV1ApplicationsApplicationIdRolesPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class RotateSecretApiV1ApplicationsApplicationIdSecretRotationsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class VerificationApplicationApiV1ApplicationsApplicationIdSupportVerificationPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

AuditEventsApiV1AuditEventsGetQuery = TypedDict('AuditEventsApiV1AuditEventsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool'], 'actor': NotRequired['str | None'], 'action': NotRequired['str | None'], 'organization_id': NotRequired['str | None']})

@dataclass(frozen=True, kw_only=True)
class AssetsAccountApiV1BrandingAssetsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListAccountApiV1ChannelsGetQuery = TypedDict('ListAccountApiV1ChannelsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None']})

@dataclass(frozen=True, kw_only=True)
class TestAccountApiV1ChannelsChannelTypeTestPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class VerifyAccountApiV1ChannelsChannelTypeVerifyPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListConnectionsApiV1ConnectionsGetQuery = TypedDict('ListConnectionsApiV1ConnectionsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool'], 'provider': NotRequired["Literal['google'] | Literal['apple'] | Literal['microsoft'] | Literal['github'] | Literal['oidc'] | Literal['saml'] | None"]})

GetActsApiV1ConsentActsGetQuery = TypedDict('GetActsApiV1ConsentActsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool'], 'subject_id': NotRequired['str | None'], 'application_id': NotRequired['str | None'], 'organization_id': NotRequired['str | None'], 'key': NotRequired['str | None'], 'version': NotRequired['int | None'], 'decision': NotRequired["Literal['accepted'] | Literal['declined'] | None"], 'scope': NotRequired["Literal['application'] | Literal['organization'] | None"], 'email': NotRequired['str | None']})

@dataclass(frozen=True, kw_only=True)
class RevokeActApiV1ConsentActsActIdRevokePostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListAccountDomainsApiV1DomainsGetQuery = TypedDict('ListAccountDomainsApiV1DomainsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class CreateAccountDomainApiV1DomainsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class VerifyAccountDomainApiV1DomainsDomainIdVerifyPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListInvitationsApiV1InvitationsGetQuery = TypedDict('ListInvitationsApiV1InvitationsGetQuery', {'organization_id': NotRequired['str | None'], 'application_id': NotRequired['str | None'], 'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class CreateInvitationApiV1InvitationsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class ResendInvitationApiV1InvitationsInvitationIdResendPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

SelfMembershipsApiV1MeMembershipsGetQuery = TypedDict('SelfMembershipsApiV1MeMembershipsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

ListMessagesApiV1MessagesGetQuery = TypedDict('ListMessagesApiV1MessagesGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool'], 'channel_type': NotRequired["Literal['email'] | Literal['sms'] | Literal['whatsapp'] | None"], 'organization_id': NotRequired['str | None'], 'application_id': NotRequired['str | None'], 'status': NotRequired['str | None'], 'recipient': NotRequired['str | None']})

ListOrganizationsApiV1OrganizationsGetQuery = TypedDict('ListOrganizationsApiV1OrganizationsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool'], 'without_admin': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class CreateOrganizationApiV1OrganizationsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListEnabledApplicationsApiV1OrganizationsOrganizationIdApplicationsGetQuery = TypedDict('ListEnabledApplicationsApiV1OrganizationsOrganizationIdApplicationsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

ListOrganizationApplicationRolesApiV1OrganizationsOrganizationIdApplicationsApplicationIdRolesGetQuery = TypedDict('ListOrganizationApplicationRolesApiV1OrganizationsOrganizationIdApplicationsApplicationIdRolesGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

ListOrganizationApiV1OrganizationsOrganizationIdChannelsGetQuery = TypedDict('ListOrganizationApiV1OrganizationsOrganizationIdChannelsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None']})

@dataclass(frozen=True, kw_only=True)
class TestOrganizationApiV1OrganizationsOrganizationIdChannelsChannelTypeTestPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class VerifyOrganizationApiV1OrganizationsOrganizationIdChannelsChannelTypeVerifyPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListOrgConnectionsApiV1OrganizationsOrganizationIdConnectionsGetQuery = TypedDict('ListOrgConnectionsApiV1OrganizationsOrganizationIdConnectionsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool'], 'provider': NotRequired["Literal['google'] | Literal['apple'] | Literal['microsoft'] | Literal['github'] | Literal['oidc'] | Literal['saml'] | None"]})

OrgListApiV1OrganizationsOrganizationIdConsentsGetQuery = TypedDict('OrgListApiV1OrganizationsOrganizationIdConsentsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class OrgCreateApiV1OrganizationsOrganizationIdConsentsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

OrgVersionsApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsGetQuery = TypedDict('OrgVersionsApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class OrgPublishApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListOrganizationDomainsApiV1OrganizationsOrganizationIdDomainsGetQuery = TypedDict('ListOrganizationDomainsApiV1OrganizationsOrganizationIdDomainsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class CreateOrganizationDomainApiV1OrganizationsOrganizationIdDomainsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class VerifyOrganizationDomainApiV1OrganizationsOrganizationIdDomainsDomainIdVerifyPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListMembershipsApiV1OrganizationsOrganizationIdMembershipsGetQuery = TypedDict('ListMembershipsApiV1OrganizationsOrganizationIdMembershipsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool'], 'administrator': NotRequired['bool | None']})

@dataclass(frozen=True, kw_only=True)
class CreateMembershipApiV1OrganizationsOrganizationIdMembershipsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

GetKeysApiV1SigningKeysGetQuery = TypedDict('GetKeysApiV1SigningKeysGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class VerificationAccountApiV1SupportVerificationPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListUsersApiV1UsersGetQuery = TypedDict('ListUsersApiV1UsersGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool'], 'status': NotRequired["Literal['pending'] | Literal['active'] | Literal['suspended'] | None"], 'mfa': NotRequired["Literal['none'] | Literal['missing_required'] | None"], 'q': NotRequired['str | None']})

@dataclass(frozen=True, kw_only=True)
class CreateUserApiV1UsersPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class DeleteUserApiV1UsersUserIdDeleteWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class ApproveUserApiV1UsersUserIdApprovePostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListUserMembershipsApiV1UsersUserIdMembershipsGetQuery = TypedDict('ListUserMembershipsApiV1UsersUserIdMembershipsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class ResetMfaApiV1UsersUserIdMfaResetPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class UnblockProcessingApiV1UsersUserIdProcessingBlockDeleteWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class BlockProcessingApiV1UsersUserIdProcessingBlockPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class IssueRecoveryApiV1UsersUserIdRecoveryPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class RejectUserApiV1UsersUserIdRejectPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListSessionsApiV1UsersUserIdSessionsGetQuery = TypedDict('ListSessionsApiV1UsersUserIdSessionsGetQuery', {'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class RevokeUserSessionsApiV1UsersUserIdSessionsRevokePostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListDeliveriesApiV1WebhookDeliveriesGetQuery = TypedDict('ListDeliveriesApiV1WebhookDeliveriesGetQuery', {'application_id': NotRequired['str | None'], 'endpoint_id': NotRequired['str | None'], 'type': NotRequired['str | None'], 'status': NotRequired["Literal['pending'] | Literal['delivered'] | Literal['exhausted'] | None"], 'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class RetryDeliveryApiV1WebhookDeliveriesDeliveryIdRetryPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

ListEndpointsApiV1WebhookEndpointsGetQuery = TypedDict('ListEndpointsApiV1WebhookEndpointsGetQuery', {'application_id': NotRequired['str | None'], 'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

@dataclass(frozen=True, kw_only=True)
class CreateEndpointApiV1WebhookEndpointsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class ChangeDestinationApiV1WebhookEndpointsEndpointIdDestinationChangesPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class RotateEndpointApiV1WebhookEndpointsEndpointIdSecretRotationsPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

@dataclass(frozen=True, kw_only=True)
class TestEndpointApiV1WebhookEndpointsEndpointIdTestPostWriteOptions(WriteOptions):
    idempotency_key: str = field()

EventTypesApiV1WebhookEventTypesGetQuery = TypedDict('EventTypesApiV1WebhookEventTypesGetQuery', {'application_id': Required['str'], 'limit': NotRequired['int'], 'cursor': NotRequired['str | None'], 'include_total': NotRequired['bool']})

class ManagementOperations:
    def __init__(self, transport: ManagementTransport) -> None:
        self._transport = transport
    async def get_account_policy_api_v1_account_policy_get(self, *, options: WriteOptions | None = None) -> ApiResult[AccountPolicyResource]:
        return cast(ApiResult[AccountPolicyResource], await self._transport.request('GET', '' + '/' + 'account-policy', None, options or WriteOptions(), None))

    async def patch_account_policy_api_v1_account_policy_patch(self, *, options: WriteOptions | None = None, body: AccountPolicyPatch) -> ApiResult[AccountPolicyResource]:
        return cast(ApiResult[AccountPolicyResource], await self._transport.request('PATCH', '' + '/' + 'account-policy', body, options or WriteOptions(), None))

    async def list_applications_api_v1_applications_get(self, *, query: ListApplicationsApiV1ApplicationsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ApplicationList]:
        return cast(ApiResult[ApplicationList], await self._transport.request('GET', '' + '/' + 'applications', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_applications_api_v1_applications_get_iterate(self, *, query: ListApplicationsApiV1ApplicationsGetQuery | None = None, identity: Callable[[Application], str | int] | None = None) -> AsyncIterator[Application]:
        return self._transport.iterate('' + '/' + 'applications', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_application_api_v1_applications_post(self, *, options: CreateApplicationApiV1ApplicationsPostWriteOptions, body: ApplicationCreate) -> ApiResult[Application]:
        return cast(ApiResult[Application], await self._transport.request('POST', '' + '/' + 'applications', body, options or WriteOptions(), None))

    async def delete_application_api_v1_applications__application_id__delete(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'applications' + '/' + quote(str(application_id), safe=''), None, options or WriteOptions(), None))

    async def get_application_api_v1_applications__application_id__get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[Application]:
        return cast(ApiResult[Application], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe=''), None, options or WriteOptions(), None))

    async def patch_application_api_v1_applications__application_id__patch(self, *, application_id: str, options: WriteOptions | None = None, body: ApplicationPatch) -> ApiResult[Application]:
        return cast(ApiResult[Application], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe=''), body, options or WriteOptions(), None))

    async def get_agent_instructions_api_v1_applications__application_id__agent_instructions_get(self, *, application_id: str, query: GetAgentInstructionsApiV1ApplicationsApplicationIdAgentInstructionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[AgentInstructionsResource]:
        return cast(ApiResult[AgentInstructionsResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'agent-instructions', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    async def get_authentication_api_v1_applications__application_id__authentication_get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[AuthenticationResource]:
        return cast(ApiResult[AuthenticationResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'authentication', None, options or WriteOptions(), None))

    async def patch_authentication_api_v1_applications__application_id__authentication_patch(self, *, application_id: str, options: WriteOptions | None = None, body: AuthenticationPatch) -> ApiResult[AuthenticationResource]:
        return cast(ApiResult[AuthenticationResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'authentication', body, options or WriteOptions(), None))

    async def get_entry_api_v1_applications__application_id__authentication_entry_get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[EntryResource]:
        return cast(ApiResult[EntryResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'authentication' + '/' + 'entry', None, options or WriteOptions(), None))

    async def patch_entry_api_v1_applications__application_id__authentication_entry_patch(self, *, application_id: str, options: WriteOptions | None = None, body: EntryPatch) -> ApiResult[EntryResource]:
        return cast(ApiResult[EntryResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'authentication' + '/' + 'entry', body, options or WriteOptions(), None))

    async def remove_application_api_v1_applications__application_id__branding_delete(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'branding', None, options or WriteOptions(), None))

    async def read_application_api_v1_applications__application_id__branding_get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'branding', None, options or WriteOptions(), None))

    async def patch_application_api_v1_applications__application_id__branding_patch(self, *, application_id: str, options: WriteOptions | None = None, body: Theme) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'branding', body, options or WriteOptions(), None))

    async def assets_application_api_v1_applications__application_id__branding_assets_post(self, *, application_id: str, options: AssetsApplicationApiV1ApplicationsApplicationIdBrandingAssetsPostWriteOptions, body: MultipartInput) -> ApiResult[AssetResource]:
        return cast(ApiResult[AssetResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'branding' + '/' + 'assets', body, options or WriteOptions(), None))

    async def language_application_api_v1_applications__application_id__branding_language_patch(self, *, application_id: str, options: WriteOptions | None = None, body: LanguagePatch) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'branding' + '/' + 'language', body, options or WriteOptions(), None))

    async def login_preview_application_api_v1_applications__application_id__branding_login_preview_post(self, *, application_id: str, options: WriteOptions | None = None, body: PreviewRequest) -> ApiResult[PreviewResponse]:
        return cast(ApiResult[PreviewResponse], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'branding' + '/' + 'login-preview', body, options or WriteOptions(), None))

    async def seal_application_api_v1_applications__application_id__branding_seal_patch(self, *, application_id: str, options: WriteOptions | None = None, body: SealPatch) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'branding' + '/' + 'seal', body, options or WriteOptions(), None))

    async def list_application_api_v1_applications__application_id__channels_get(self, *, application_id: str, query: ListApplicationApiV1ApplicationsApplicationIdChannelsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ChannelList]:
        return cast(ApiResult[ChannelList], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'channels', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_application_api_v1_applications__application_id__channels_get_iterate(self, *, application_id: str, query: ListApplicationApiV1ApplicationsApplicationIdChannelsGetQuery | None = None, identity: Callable[[ChannelResource], str | int]) -> AsyncIterator[ChannelResource]:
        return self._transport.iterate('' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'channels', cast(Mapping[str, QueryValue], query), identity=identity)

    async def remove_application_api_v1_applications__application_id__channels__channel_type__delete(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), None, options or WriteOptions(), None))

    async def read_application_api_v1_applications__application_id__channels__channel_type__get(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: WriteOptions | None = None) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), None, options or WriteOptions(), None))

    async def patch_application_api_v1_applications__application_id__channels__channel_type__patch(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: WriteOptions | None = None, body: ChannelPatch) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), body, options or WriteOptions(), None))

    async def identity_application_api_v1_applications__application_id__channels__channel_type__identity_patch(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: WriteOptions | None = None, body: EmailIdentity | WhatsappIdentity) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'identity', body, options or WriteOptions(), None))

    async def test_application_api_v1_applications__application_id__channels__channel_type__test_post(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: TestApplicationApiV1ApplicationsApplicationIdChannelsChannelTypeTestPostWriteOptions, body: Empty | PhoneStart | PhoneConfirm) -> ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult]:
        return cast(ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'test', body, options or WriteOptions(), None))

    async def verify_application_api_v1_applications__application_id__channels__channel_type__verify_post(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: VerifyApplicationApiV1ApplicationsApplicationIdChannelsChannelTypeVerifyPostWriteOptions, body: Empty) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'verify', body, options or WriteOptions(), None))

    async def get_claims_api_v1_applications__application_id__claims_get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[ClaimsResource]:
        return cast(ApiResult[ClaimsResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'claims', None, options or WriteOptions(), None))

    async def patch_claims_api_v1_applications__application_id__claims_patch(self, *, application_id: str, options: WriteOptions | None = None, body: ClaimsPut) -> ApiResult[ClaimsResource]:
        return cast(ApiResult[ClaimsResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'claims', body, options or WriteOptions(), None))

    async def get_receipt_api_v1_applications__application_id__consent_receipt_get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[ReceiptResource]:
        return cast(ApiResult[ReceiptResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consent-receipt', None, options or WriteOptions(), None))

    async def patch_receipt_api_v1_applications__application_id__consent_receipt_patch(self, *, application_id: str, options: WriteOptions | None = None, body: ReceiptPatch) -> ApiResult[ReceiptResource]:
        return cast(ApiResult[ReceiptResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consent-receipt', body, options or WriteOptions(), None))

    async def app_list_api_v1_applications__application_id__consents_get(self, *, application_id: str, query: AppListApiV1ApplicationsApplicationIdConsentsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[TermList]:
        return cast(ApiResult[TermList], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def app_list_api_v1_applications__application_id__consents_get_iterate(self, *, application_id: str, query: AppListApiV1ApplicationsApplicationIdConsentsGetQuery | None = None, identity: Callable[[TermResource], str | int] | None = None) -> AsyncIterator[TermResource]:
        return self._transport.iterate('' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def app_create_api_v1_applications__application_id__consents_post(self, *, application_id: str, options: AppCreateApiV1ApplicationsApplicationIdConsentsPostWriteOptions, body: TermCreate) -> ApiResult[TermResource]:
        return cast(ApiResult[TermResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents', body, options or WriteOptions(), None))

    async def app_retire_api_v1_applications__application_id__consents__consent_id__delete(self, *, application_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe=''), None, options or WriteOptions(), None))

    async def app_read_api_v1_applications__application_id__consents__consent_id__get(self, *, application_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[TermResource]:
        return cast(ApiResult[TermResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe=''), None, options or WriteOptions(), None))

    async def app_patch_api_v1_applications__application_id__consents__consent_id__patch(self, *, application_id: str, consent_id: str, options: WriteOptions | None = None, body: TermPatch) -> ApiResult[TermMutationResponse]:
        return cast(ApiResult[TermMutationResponse], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe=''), body, options or WriteOptions(), None))

    async def app_impact_api_v1_applications__application_id__consents__consent_id__impact_get(self, *, application_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[ImpactResource]:
        return cast(ApiResult[ImpactResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'impact', None, options or WriteOptions(), None))

    async def app_versions_api_v1_applications__application_id__consents__consent_id__versions_get(self, *, application_id: str, consent_id: str, query: AppVersionsApiV1ApplicationsApplicationIdConsentsConsentIdVersionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[VersionList]:
        return cast(ApiResult[VersionList], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'versions', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def app_versions_api_v1_applications__application_id__consents__consent_id__versions_get_iterate(self, *, application_id: str, consent_id: str, query: AppVersionsApiV1ApplicationsApplicationIdConsentsConsentIdVersionsGetQuery | None = None, identity: Callable[[VersionResource], str | int]) -> AsyncIterator[VersionResource]:
        return self._transport.iterate('' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'versions', cast(Mapping[str, QueryValue], query), identity=identity)

    async def app_publish_api_v1_applications__application_id__consents__consent_id__versions_post(self, *, application_id: str, consent_id: str, options: AppPublishApiV1ApplicationsApplicationIdConsentsConsentIdVersionsPostWriteOptions, body: MultipartInput) -> ApiResult[VersionResource]:
        return cast(ApiResult[VersionResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'versions', body, options or WriteOptions(), None))

    async def app_version_api_v1_applications__application_id__consents__consent_id__versions__version__get(self, *, application_id: str, consent_id: str, version: int, options: WriteOptions | None = None) -> ApiResult[VersionResource]:
        return cast(ApiResult[VersionResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'versions' + '/' + quote(str(version), safe=''), None, options or WriteOptions(), None))

    async def list_application_domains_api_v1_applications__application_id__domains_get(self, *, application_id: str, query: ListApplicationDomainsApiV1ApplicationsApplicationIdDomainsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[DomainList]:
        return cast(ApiResult[DomainList], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'domains', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_application_domains_api_v1_applications__application_id__domains_get_iterate(self, *, application_id: str, query: ListApplicationDomainsApiV1ApplicationsApplicationIdDomainsGetQuery | None = None, identity: Callable[[DomainResource], str | int] | None = None) -> AsyncIterator[DomainResource]:
        return self._transport.iterate('' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'domains', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_application_domain_api_v1_applications__application_id__domains_post(self, *, application_id: str, options: CreateApplicationDomainApiV1ApplicationsApplicationIdDomainsPostWriteOptions, body: DomainCreate) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'domains', body, options or WriteOptions(), None))

    async def delete_application_domain_api_v1_applications__application_id__domains__domain_id__delete(self, *, domain_id: str, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'domains' + '/' + quote(str(domain_id), safe=''), None, options or WriteOptions(), None))

    async def get_application_domain_api_v1_applications__application_id__domains__domain_id__get(self, *, domain_id: str, application_id: str, options: WriteOptions | None = None) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'domains' + '/' + quote(str(domain_id), safe=''), None, options or WriteOptions(), None))

    async def activate_application_domain_api_v1_applications__application_id__domains__domain_id__activate_post(self, *, application_id: str, domain_id: str, options: ActivateApplicationDomainApiV1ApplicationsApplicationIdDomainsDomainIdActivatePostWriteOptions, body: Empty) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'domains' + '/' + quote(str(domain_id), safe='') + '/' + 'activate', body, options or WriteOptions(), None))

    async def verify_application_domain_api_v1_applications__application_id__domains__domain_id__verify_post(self, *, domain_id: str, application_id: str, options: VerifyApplicationDomainApiV1ApplicationsApplicationIdDomainsDomainIdVerifyPostWriteOptions, body: Empty) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'domains' + '/' + quote(str(domain_id), safe='') + '/' + 'verify', body, options or WriteOptions(), None))

    async def list_permissions_api_v1_applications__application_id__permissions_get(self, *, application_id: str, query: ListPermissionsApiV1ApplicationsApplicationIdPermissionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[PermissionList]:
        return cast(ApiResult[PermissionList], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'permissions', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_permissions_api_v1_applications__application_id__permissions_get_iterate(self, *, application_id: str, query: ListPermissionsApiV1ApplicationsApplicationIdPermissionsGetQuery | None = None, identity: Callable[[PermissionResource], str | int] | None = None) -> AsyncIterator[PermissionResource]:
        return self._transport.iterate('' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'permissions', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def put_permissions_api_v1_applications__application_id__permissions_put(self, *, application_id: str, options: WriteOptions | None = None, body: PermissionsPut) -> ApiResult[PermissionsResource]:
        return cast(ApiResult[PermissionsResource], await self._transport.request('PUT', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'permissions', body, options or WriteOptions(), None))

    async def list_roles_api_v1_applications__application_id__roles_get(self, *, application_id: str, query: ListRolesApiV1ApplicationsApplicationIdRolesGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[RoleList]:
        return cast(ApiResult[RoleList], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'roles', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_roles_api_v1_applications__application_id__roles_get_iterate(self, *, application_id: str, query: ListRolesApiV1ApplicationsApplicationIdRolesGetQuery | None = None, identity: Callable[[RoleResource], str | int] | None = None) -> AsyncIterator[RoleResource]:
        return self._transport.iterate('' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'roles', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_role_api_v1_applications__application_id__roles_post(self, *, application_id: str, options: CreateRoleApiV1ApplicationsApplicationIdRolesPostWriteOptions, body: RoleCreate) -> ApiResult[RoleResource]:
        return cast(ApiResult[RoleResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'roles', body, options or WriteOptions(), None))

    async def delete_role_api_v1_applications__application_id__roles__role_id__delete(self, *, application_id: str, role_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'roles' + '/' + quote(str(role_id), safe=''), None, options or WriteOptions(), None))

    async def get_role_api_v1_applications__application_id__roles__role_id__get(self, *, application_id: str, role_id: str, options: WriteOptions | None = None) -> ApiResult[RoleResource]:
        return cast(ApiResult[RoleResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'roles' + '/' + quote(str(role_id), safe=''), None, options or WriteOptions(), None))

    async def patch_role_api_v1_applications__application_id__roles__role_id__patch(self, *, application_id: str, role_id: str, options: WriteOptions | None = None, body: RolePatch) -> ApiResult[RoleResource]:
        return cast(ApiResult[RoleResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'roles' + '/' + quote(str(role_id), safe=''), body, options or WriteOptions(), None))

    async def rotate_secret_api_v1_applications__application_id__secret_rotations_post(self, *, application_id: str, options: RotateSecretApiV1ApplicationsApplicationIdSecretRotationsPostWriteOptions, body: RotationCreate) -> ApiResult[StwrdIdpAdminApplicationConfigurationRotationResource]:
        return cast(ApiResult[StwrdIdpAdminApplicationConfigurationRotationResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'secret-rotations', body, options or WriteOptions(), None))

    async def reveal_secret_api_v1_applications__application_id__secret_reveal_post(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[StwrdIdpAdminApplicationConfigurationSecretResource]:
        return cast(ApiResult[StwrdIdpAdminApplicationConfigurationSecretResource], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'secret' + '/' + 'reveal', None, options or WriteOptions(), None))

    async def remove_application_api_v1_applications__application_id__support_delete(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'support', None, options or WriteOptions(), None))

    async def read_application_api_v1_applications__application_id__support_get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[SupportResource]:
        return cast(ApiResult[SupportResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'support', None, options or WriteOptions(), None))

    async def patch_application_api_v1_applications__application_id__support_patch(self, *, application_id: str, options: WriteOptions | None = None, body: SupportPatch) -> ApiResult[SupportResource]:
        return cast(ApiResult[SupportResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'support', body, options or WriteOptions(), None))

    async def verification_application_api_v1_applications__application_id__support_verification_post(self, *, application_id: str, options: VerificationApplicationApiV1ApplicationsApplicationIdSupportVerificationPostWriteOptions, body: EmptyRequest) -> ApiResult[VerificationQueued]:
        return cast(ApiResult[VerificationQueued], await self._transport.request('POST', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'support' + '/' + 'verification', body, options or WriteOptions(), None))

    async def get_test_login_api_v1_applications__application_id__test_login_get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[TestLoginResource]:
        return cast(ApiResult[TestLoginResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'test-login', None, options or WriteOptions(), None))

    async def get_tokens_api_v1_applications__application_id__tokens_get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[TokensResource]:
        return cast(ApiResult[TokensResource], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'tokens', None, options or WriteOptions(), None))

    async def patch_tokens_api_v1_applications__application_id__tokens_patch(self, *, application_id: str, options: WriteOptions | None = None, body: TokensPatch) -> ApiResult[TokensResource]:
        return cast(ApiResult[TokensResource], await self._transport.request('PATCH', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'tokens', body, options or WriteOptions(), None))

    async def delete_user_roles_api_v1_applications__application_id__users__user_id__roles_delete(self, *, application_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'roles', None, options or WriteOptions(), None))

    async def get_user_roles_api_v1_applications__application_id__users__user_id__roles_get(self, *, application_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[AssignedAccess]:
        return cast(ApiResult[AssignedAccess], await self._transport.request('GET', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'roles', None, options or WriteOptions(), None))

    async def put_user_roles_api_v1_applications__application_id__users__user_id__roles_put(self, *, application_id: str, user_id: str, options: WriteOptions | None = None, body: RolesPut) -> ApiResult[AssignedAccess]:
        return cast(ApiResult[AssignedAccess], await self._transport.request('PUT', '' + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'roles', body, options or WriteOptions(), None))

    async def audit_events_api_v1_audit_events_get(self, *, query: AuditEventsApiV1AuditEventsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[AuditEventList]:
        return cast(ApiResult[AuditEventList], await self._transport.request('GET', '' + '/' + 'audit-events', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def audit_events_api_v1_audit_events_get_iterate(self, *, query: AuditEventsApiV1AuditEventsGetQuery | None = None, identity: Callable[[AuditEventResource], str | int] | None = None) -> AsyncIterator[AuditEventResource]:
        return self._transport.iterate('' + '/' + 'audit-events', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def remove_account_api_v1_branding_delete(self, *, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'branding', None, options or WriteOptions(), None))

    async def read_account_api_v1_branding_get(self, *, options: WriteOptions | None = None) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('GET', '' + '/' + 'branding', None, options or WriteOptions(), None))

    async def patch_account_api_v1_branding_patch(self, *, options: WriteOptions | None = None, body: Theme) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('PATCH', '' + '/' + 'branding', body, options or WriteOptions(), None))

    async def assets_account_api_v1_branding_assets_post(self, *, options: AssetsAccountApiV1BrandingAssetsPostWriteOptions, body: MultipartInput) -> ApiResult[AssetResource]:
        return cast(ApiResult[AssetResource], await self._transport.request('POST', '' + '/' + 'branding' + '/' + 'assets', body, options or WriteOptions(), None))

    async def login_preview_account_api_v1_branding_login_preview_post(self, *, options: WriteOptions | None = None, body: PreviewRequest) -> ApiResult[PreviewResponse]:
        return cast(ApiResult[PreviewResponse], await self._transport.request('POST', '' + '/' + 'branding' + '/' + 'login-preview', body, options or WriteOptions(), None))

    async def seal_account_api_v1_branding_seal_patch(self, *, options: WriteOptions | None = None, body: SealPatch) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('PATCH', '' + '/' + 'branding' + '/' + 'seal', body, options or WriteOptions(), None))

    async def list_account_api_v1_channels_get(self, *, query: ListAccountApiV1ChannelsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ChannelList]:
        return cast(ApiResult[ChannelList], await self._transport.request('GET', '' + '/' + 'channels', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_account_api_v1_channels_get_iterate(self, *, query: ListAccountApiV1ChannelsGetQuery | None = None, identity: Callable[[ChannelResource], str | int]) -> AsyncIterator[ChannelResource]:
        return self._transport.iterate('' + '/' + 'channels', cast(Mapping[str, QueryValue], query), identity=identity)

    async def remove_account_api_v1_channels__channel_type__delete(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), None, options or WriteOptions(), None))

    async def read_account_api_v1_channels__channel_type__get(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: WriteOptions | None = None) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('GET', '' + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), None, options or WriteOptions(), None))

    async def patch_account_api_v1_channels__channel_type__patch(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: WriteOptions | None = None, body: ChannelPatch) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('PATCH', '' + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), body, options or WriteOptions(), None))

    async def identity_account_api_v1_channels__channel_type__identity_patch(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: WriteOptions | None = None, body: EmailIdentity | WhatsappIdentity) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('PATCH', '' + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'identity', body, options or WriteOptions(), None))

    async def test_account_api_v1_channels__channel_type__test_post(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: TestAccountApiV1ChannelsChannelTypeTestPostWriteOptions, body: Empty | PhoneStart | PhoneConfirm) -> ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult]:
        return cast(ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult], await self._transport.request('POST', '' + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'test', body, options or WriteOptions(), None))

    async def verify_account_api_v1_channels__channel_type__verify_post(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: VerifyAccountApiV1ChannelsChannelTypeVerifyPostWriteOptions, body: Empty) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('POST', '' + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'verify', body, options or WriteOptions(), None))

    async def list_connections_api_v1_connections_get(self, *, query: ListConnectionsApiV1ConnectionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ConnectionList]:
        return cast(ApiResult[ConnectionList], await self._transport.request('GET', '' + '/' + 'connections', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_connections_api_v1_connections_get_iterate(self, *, query: ListConnectionsApiV1ConnectionsGetQuery | None = None, identity: Callable[[ConnectionResource], str | int] | None = None) -> AsyncIterator[ConnectionResource]:
        return self._transport.iterate('' + '/' + 'connections', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_connection_api_v1_connections_post(self, *, options: WriteOptions | None = None, body: ConnectionCreate) -> ApiResult[ConnectionResource]:
        return cast(ApiResult[ConnectionResource], await self._transport.request('POST', '' + '/' + 'connections', body, options or WriteOptions(), None))

    async def delete_connection_api_v1_connections__connection_id__delete(self, *, connection_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'connections' + '/' + quote(str(connection_id), safe=''), None, options or WriteOptions(), None))

    async def get_connection_api_v1_connections__connection_id__get(self, *, connection_id: str, options: WriteOptions | None = None) -> ApiResult[ConnectionResource]:
        return cast(ApiResult[ConnectionResource], await self._transport.request('GET', '' + '/' + 'connections' + '/' + quote(str(connection_id), safe=''), None, options or WriteOptions(), None))

    async def patch_connection_api_v1_connections__connection_id__patch(self, *, connection_id: str, options: WriteOptions | None = None, body: ConnectionPatch) -> ApiResult[ConnectionResource]:
        return cast(ApiResult[ConnectionResource], await self._transport.request('PATCH', '' + '/' + 'connections' + '/' + quote(str(connection_id), safe=''), body, options or WriteOptions(), None))

    async def get_acts_api_v1_consent_acts_get(self, *, query: GetActsApiV1ConsentActsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ActList]:
        return cast(ApiResult[ActList], await self._transport.request('GET', '' + '/' + 'consent-acts', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def get_acts_api_v1_consent_acts_get_iterate(self, *, query: GetActsApiV1ConsentActsGetQuery | None = None, identity: Callable[[ActResource], str | int] | None = None) -> AsyncIterator[ActResource]:
        return self._transport.iterate('' + '/' + 'consent-acts', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def get_act_api_v1_consent_acts__act_id__get(self, *, act_id: str, options: WriteOptions | None = None) -> ApiResult[ActResource]:
        return cast(ApiResult[ActResource], await self._transport.request('GET', '' + '/' + 'consent-acts' + '/' + quote(str(act_id), safe=''), None, options or WriteOptions(), None))

    async def revoke_act_api_v1_consent_acts__act_id__revoke_post(self, *, act_id: str, options: RevokeActApiV1ConsentActsActIdRevokePostWriteOptions, body: Empty) -> ApiResult[ActResource]:
        return cast(ApiResult[ActResource], await self._transport.request('POST', '' + '/' + 'consent-acts' + '/' + quote(str(act_id), safe='') + '/' + 'revoke', body, options or WriteOptions(), None))

    async def get_document_api_v1_consent_documents__digest__get(self, *, digest: str, options: WriteOptions | None = None) -> ApiResult[bytes]:
        return cast(ApiResult[bytes], await self._transport.request('GET', '' + '/' + 'consent-documents' + '/' + quote(str(digest), safe=''), None, replace(options or WriteOptions(), response_type='bytes'), None))

    async def get_retention_api_v1_consent_retention_get(self, *, options: WriteOptions | None = None) -> ApiResult[RetentionResource]:
        return cast(ApiResult[RetentionResource], await self._transport.request('GET', '' + '/' + 'consent-retention', None, options or WriteOptions(), None))

    async def patch_retention_api_v1_consent_retention_patch(self, *, options: WriteOptions | None = None, body: RetentionPatch) -> ApiResult[RetentionResource]:
        return cast(ApiResult[RetentionResource], await self._transport.request('PATCH', '' + '/' + 'consent-retention', body, options or WriteOptions(), None))

    async def credential_context_api_v1_context_get(self, *, options: WriteOptions | None = None) -> ApiResult[ContextResource]:
        return cast(ApiResult[ContextResource], await self._transport.request('GET', '' + '/' + 'context', None, options or WriteOptions(), None))

    async def list_account_domains_api_v1_domains_get(self, *, query: ListAccountDomainsApiV1DomainsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[DomainList]:
        return cast(ApiResult[DomainList], await self._transport.request('GET', '' + '/' + 'domains', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_account_domains_api_v1_domains_get_iterate(self, *, query: ListAccountDomainsApiV1DomainsGetQuery | None = None, identity: Callable[[DomainResource], str | int] | None = None) -> AsyncIterator[DomainResource]:
        return self._transport.iterate('' + '/' + 'domains', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_account_domain_api_v1_domains_post(self, *, options: CreateAccountDomainApiV1DomainsPostWriteOptions, body: DomainCreate) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('POST', '' + '/' + 'domains', body, options or WriteOptions(), None))

    async def delete_account_domain_api_v1_domains__domain_id__delete(self, *, domain_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'domains' + '/' + quote(str(domain_id), safe=''), None, options or WriteOptions(), None))

    async def get_account_domain_api_v1_domains__domain_id__get(self, *, domain_id: str, options: WriteOptions | None = None) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('GET', '' + '/' + 'domains' + '/' + quote(str(domain_id), safe=''), None, options or WriteOptions(), None))

    async def verify_account_domain_api_v1_domains__domain_id__verify_post(self, *, domain_id: str, options: VerifyAccountDomainApiV1DomainsDomainIdVerifyPostWriteOptions, body: Empty) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('POST', '' + '/' + 'domains' + '/' + quote(str(domain_id), safe='') + '/' + 'verify', body, options or WriteOptions(), None))

    async def list_invitations_api_v1_invitations_get(self, *, query: ListInvitationsApiV1InvitationsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[InvitationList]:
        return cast(ApiResult[InvitationList], await self._transport.request('GET', '' + '/' + 'invitations', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_invitations_api_v1_invitations_get_iterate(self, *, query: ListInvitationsApiV1InvitationsGetQuery | None = None, identity: Callable[[InvitationResource], str | int] | None = None) -> AsyncIterator[InvitationResource]:
        return self._transport.iterate('' + '/' + 'invitations', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_invitation_api_v1_invitations_post(self, *, options: CreateInvitationApiV1InvitationsPostWriteOptions, body: InvitationCreate) -> ApiResult[InvitationResource]:
        return cast(ApiResult[InvitationResource], await self._transport.request('POST', '' + '/' + 'invitations', body, options or WriteOptions(), None))

    async def cancel_invitation_api_v1_invitations__invitation_id__delete(self, *, invitation_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'invitations' + '/' + quote(str(invitation_id), safe=''), None, options or WriteOptions(), None))

    async def get_invitation_api_v1_invitations__invitation_id__get(self, *, invitation_id: str, options: WriteOptions | None = None) -> ApiResult[InvitationResource]:
        return cast(ApiResult[InvitationResource], await self._transport.request('GET', '' + '/' + 'invitations' + '/' + quote(str(invitation_id), safe=''), None, options or WriteOptions(), None))

    async def resend_invitation_api_v1_invitations__invitation_id__resend_post(self, *, invitation_id: str, options: ResendInvitationApiV1InvitationsInvitationIdResendPostWriteOptions) -> ApiResult[InvitationResource]:
        return cast(ApiResult[InvitationResource], await self._transport.request('POST', '' + '/' + 'invitations' + '/' + quote(str(invitation_id), safe='') + '/' + 'resend', None, options or WriteOptions(), None))

    async def self_user_api_v1_me_get(self, *, options: WriteOptions | None = None) -> ApiResult[SelfUserResource]:
        return cast(ApiResult[SelfUserResource], await self._transport.request('GET', '' + '/' + 'me', None, options or WriteOptions(), None))

    async def self_memberships_api_v1_me_memberships_get(self, *, query: SelfMembershipsApiV1MeMembershipsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[SelfMembershipList]:
        return cast(ApiResult[SelfMembershipList], await self._transport.request('GET', '' + '/' + 'me' + '/' + 'memberships', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def self_memberships_api_v1_me_memberships_get_iterate(self, *, query: SelfMembershipsApiV1MeMembershipsGetQuery | None = None, identity: Callable[[SelfMembership], str | int]) -> AsyncIterator[SelfMembership]:
        return self._transport.iterate('' + '/' + 'me' + '/' + 'memberships', cast(Mapping[str, QueryValue], query), identity=identity)

    async def list_messages_api_v1_messages_get(self, *, query: ListMessagesApiV1MessagesGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[MessageList]:
        return cast(ApiResult[MessageList], await self._transport.request('GET', '' + '/' + 'messages', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_messages_api_v1_messages_get_iterate(self, *, query: ListMessagesApiV1MessagesGetQuery | None = None, identity: Callable[[MessageResource], str | int] | None = None) -> AsyncIterator[MessageResource]:
        return self._transport.iterate('' + '/' + 'messages', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def get_policy_api_v1_organization_admin_policy_get(self, *, options: WriteOptions | None = None) -> ApiResult[AdministrativePolicy]:
        return cast(ApiResult[AdministrativePolicy], await self._transport.request('GET', '' + '/' + 'organization-admin-policy', None, options or WriteOptions(), None))

    async def patch_policy_api_v1_organization_admin_policy_patch(self, *, options: WriteOptions | None = None, body: AdministrativePolicyPatch) -> ApiResult[AdministrativePolicy]:
        return cast(ApiResult[AdministrativePolicy], await self._transport.request('PATCH', '' + '/' + 'organization-admin-policy', body, options or WriteOptions(), None))

    async def list_organizations_api_v1_organizations_get(self, *, query: ListOrganizationsApiV1OrganizationsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[OrganizationList]:
        return cast(ApiResult[OrganizationList], await self._transport.request('GET', '' + '/' + 'organizations', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_organizations_api_v1_organizations_get_iterate(self, *, query: ListOrganizationsApiV1OrganizationsGetQuery | None = None, identity: Callable[[OrganizationResource], str | int] | None = None) -> AsyncIterator[OrganizationResource]:
        return self._transport.iterate('' + '/' + 'organizations', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_organization_api_v1_organizations_post(self, *, options: CreateOrganizationApiV1OrganizationsPostWriteOptions, body: OrganizationCreate) -> ApiResult[OrganizationResource]:
        return cast(ApiResult[OrganizationResource], await self._transport.request('POST', '' + '/' + 'organizations', body, options or WriteOptions(), None))

    async def delete_organization_api_v1_organizations__organization_id__delete(self, *, organization_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe=''), None, options or WriteOptions(), None))

    async def get_organization_api_v1_organizations__organization_id__get(self, *, organization_id: str, options: WriteOptions | None = None) -> ApiResult[OrganizationResource]:
        return cast(ApiResult[OrganizationResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe=''), None, options or WriteOptions(), None))

    async def patch_organization_api_v1_organizations__organization_id__patch(self, *, organization_id: str, options: WriteOptions | None = None, body: OrganizationPatch) -> ApiResult[OrganizationResource]:
        return cast(ApiResult[OrganizationResource], await self._transport.request('PATCH', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe=''), body, options or WriteOptions(), None))

    async def list_enabled_applications_api_v1_organizations__organization_id__applications_get(self, *, organization_id: str, query: ListEnabledApplicationsApiV1OrganizationsOrganizationIdApplicationsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[EnabledApplicationList]:
        return cast(ApiResult[EnabledApplicationList], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_enabled_applications_api_v1_organizations__organization_id__applications_get_iterate(self, *, organization_id: str, query: ListEnabledApplicationsApiV1OrganizationsOrganizationIdApplicationsGetQuery | None = None, identity: Callable[[EnabledApplication], str | int]) -> AsyncIterator[EnabledApplication]:
        return self._transport.iterate('' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications', cast(Mapping[str, QueryValue], query), identity=identity)

    async def disable_application_api_v1_organizations__organization_id__applications__application_id__delete(self, *, organization_id: str, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications' + '/' + quote(str(application_id), safe=''), None, options or WriteOptions(), None))

    async def get_enabled_application_api_v1_organizations__organization_id__applications__application_id__get(self, *, organization_id: str, application_id: str, options: WriteOptions | None = None) -> ApiResult[EnabledApplication]:
        return cast(ApiResult[EnabledApplication], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications' + '/' + quote(str(application_id), safe=''), None, options or WriteOptions(), None))

    async def enable_application_api_v1_organizations__organization_id__applications__application_id__put(self, *, organization_id: str, application_id: str, options: WriteOptions | None = None, body: EnableApplication) -> ApiResult[EnabledApplication]:
        return cast(ApiResult[EnabledApplication], await self._transport.request('PUT', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications' + '/' + quote(str(application_id), safe=''), body, options or WriteOptions(), None))

    async def delete_member_access_api_v1_organizations__organization_id__applications__application_id__members__user_id__delete(self, *, organization_id: str, application_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'members' + '/' + quote(str(user_id), safe=''), None, options or WriteOptions(), None))

    async def get_member_access_api_v1_organizations__organization_id__applications__application_id__members__user_id__get(self, *, organization_id: str, application_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[AssignedAccess]:
        return cast(ApiResult[AssignedAccess], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'members' + '/' + quote(str(user_id), safe=''), None, options or WriteOptions(), None))

    async def put_member_access_api_v1_organizations__organization_id__applications__application_id__members__user_id__put(self, *, organization_id: str, application_id: str, user_id: str, options: WriteOptions | None = None, body: RolesPut) -> ApiResult[AssignedAccess]:
        return cast(ApiResult[AssignedAccess], await self._transport.request('PUT', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'members' + '/' + quote(str(user_id), safe=''), body, options or WriteOptions(), None))

    async def list_organization_application_roles_api_v1_organizations__organization_id__applications__application_id__roles_get(self, *, organization_id: str, application_id: str, query: ListOrganizationApplicationRolesApiV1OrganizationsOrganizationIdApplicationsApplicationIdRolesGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[RoleList]:
        return cast(ApiResult[RoleList], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'roles', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_organization_application_roles_api_v1_organizations__organization_id__applications__application_id__roles_get_iterate(self, *, organization_id: str, application_id: str, query: ListOrganizationApplicationRolesApiV1OrganizationsOrganizationIdApplicationsApplicationIdRolesGetQuery | None = None, identity: Callable[[RoleResource], str | int] | None = None) -> AsyncIterator[RoleResource]:
        return self._transport.iterate('' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'applications' + '/' + quote(str(application_id), safe='') + '/' + 'roles', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def remove_organization_api_v1_organizations__organization_id__branding_delete(self, *, organization_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'branding', None, options or WriteOptions(), None))

    async def read_organization_api_v1_organizations__organization_id__branding_get(self, *, organization_id: str, options: WriteOptions | None = None) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'branding', None, options or WriteOptions(), None))

    async def patch_organization_api_v1_organizations__organization_id__branding_patch(self, *, organization_id: str, options: WriteOptions | None = None, body: Theme) -> ApiResult[BrandingResource]:
        return cast(ApiResult[BrandingResource], await self._transport.request('PATCH', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'branding', body, options or WriteOptions(), None))

    async def list_organization_api_v1_organizations__organization_id__channels_get(self, *, organization_id: str, query: ListOrganizationApiV1OrganizationsOrganizationIdChannelsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ChannelList]:
        return cast(ApiResult[ChannelList], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'channels', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_organization_api_v1_organizations__organization_id__channels_get_iterate(self, *, organization_id: str, query: ListOrganizationApiV1OrganizationsOrganizationIdChannelsGetQuery | None = None, identity: Callable[[ChannelResource], str | int]) -> AsyncIterator[ChannelResource]:
        return self._transport.iterate('' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'channels', cast(Mapping[str, QueryValue], query), identity=identity)

    async def remove_organization_api_v1_organizations__organization_id__channels__channel_type__delete(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), None, options or WriteOptions(), None))

    async def read_organization_api_v1_organizations__organization_id__channels__channel_type__get(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: WriteOptions | None = None) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), None, options or WriteOptions(), None))

    async def patch_organization_api_v1_organizations__organization_id__channels__channel_type__patch(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: WriteOptions | None = None, body: ChannelPatch) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('PATCH', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe=''), body, options or WriteOptions(), None))

    async def identity_organization_api_v1_organizations__organization_id__channels__channel_type__identity_patch(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: WriteOptions | None = None, body: EmailIdentity | WhatsappIdentity) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('PATCH', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'identity', body, options or WriteOptions(), None))

    async def test_organization_api_v1_organizations__organization_id__channels__channel_type__test_post(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: TestOrganizationApiV1OrganizationsOrganizationIdChannelsChannelTypeTestPostWriteOptions, body: Empty | PhoneStart | PhoneConfirm) -> ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult]:
        return cast(ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult], await self._transport.request('POST', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'test', body, options or WriteOptions(), None))

    async def verify_organization_api_v1_organizations__organization_id__channels__channel_type__verify_post(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: VerifyOrganizationApiV1OrganizationsOrganizationIdChannelsChannelTypeVerifyPostWriteOptions, body: Empty) -> ApiResult[ChannelResource]:
        return cast(ApiResult[ChannelResource], await self._transport.request('POST', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'channels' + '/' + quote(str(channel_type), safe='') + '/' + 'verify', body, options or WriteOptions(), None))

    async def list_org_connections_api_v1_organizations__organization_id__connections_get(self, *, organization_id: str, query: ListOrgConnectionsApiV1OrganizationsOrganizationIdConnectionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ConnectionList]:
        return cast(ApiResult[ConnectionList], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'connections', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_org_connections_api_v1_organizations__organization_id__connections_get_iterate(self, *, organization_id: str, query: ListOrgConnectionsApiV1OrganizationsOrganizationIdConnectionsGetQuery | None = None, identity: Callable[[ConnectionResource], str | int] | None = None) -> AsyncIterator[ConnectionResource]:
        return self._transport.iterate('' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'connections', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_org_connection_api_v1_organizations__organization_id__connections_post(self, *, organization_id: str, options: WriteOptions | None = None, body: ConnectionCreate) -> ApiResult[ConnectionResource]:
        return cast(ApiResult[ConnectionResource], await self._transport.request('POST', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'connections', body, options or WriteOptions(), None))

    async def delete_org_connection_api_v1_organizations__organization_id__connections__connection_id__delete(self, *, organization_id: str, connection_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'connections' + '/' + quote(str(connection_id), safe=''), None, options or WriteOptions(), None))

    async def get_org_connection_api_v1_organizations__organization_id__connections__connection_id__get(self, *, organization_id: str, connection_id: str, options: WriteOptions | None = None) -> ApiResult[ConnectionResource]:
        return cast(ApiResult[ConnectionResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'connections' + '/' + quote(str(connection_id), safe=''), None, options or WriteOptions(), None))

    async def patch_org_connection_api_v1_organizations__organization_id__connections__connection_id__patch(self, *, organization_id: str, connection_id: str, options: WriteOptions | None = None, body: ConnectionPatch) -> ApiResult[ConnectionResource]:
        return cast(ApiResult[ConnectionResource], await self._transport.request('PATCH', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'connections' + '/' + quote(str(connection_id), safe=''), body, options or WriteOptions(), None))

    async def org_list_api_v1_organizations__organization_id__consents_get(self, *, organization_id: str, query: OrgListApiV1OrganizationsOrganizationIdConsentsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[TermList]:
        return cast(ApiResult[TermList], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def org_list_api_v1_organizations__organization_id__consents_get_iterate(self, *, organization_id: str, query: OrgListApiV1OrganizationsOrganizationIdConsentsGetQuery | None = None, identity: Callable[[TermResource], str | int] | None = None) -> AsyncIterator[TermResource]:
        return self._transport.iterate('' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def org_create_api_v1_organizations__organization_id__consents_post(self, *, organization_id: str, options: OrgCreateApiV1OrganizationsOrganizationIdConsentsPostWriteOptions, body: TermCreate) -> ApiResult[TermResource]:
        return cast(ApiResult[TermResource], await self._transport.request('POST', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents', body, options or WriteOptions(), None))

    async def org_retire_api_v1_organizations__organization_id__consents__consent_id__delete(self, *, organization_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe=''), None, options or WriteOptions(), None))

    async def org_read_api_v1_organizations__organization_id__consents__consent_id__get(self, *, organization_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[TermResource]:
        return cast(ApiResult[TermResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe=''), None, options or WriteOptions(), None))

    async def org_patch_api_v1_organizations__organization_id__consents__consent_id__patch(self, *, organization_id: str, consent_id: str, options: WriteOptions | None = None, body: TermPatch) -> ApiResult[TermMutationResponse]:
        return cast(ApiResult[TermMutationResponse], await self._transport.request('PATCH', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe=''), body, options or WriteOptions(), None))

    async def org_impact_api_v1_organizations__organization_id__consents__consent_id__impact_get(self, *, organization_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[ImpactResource]:
        return cast(ApiResult[ImpactResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'impact', None, options or WriteOptions(), None))

    async def org_versions_api_v1_organizations__organization_id__consents__consent_id__versions_get(self, *, organization_id: str, consent_id: str, query: OrgVersionsApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[VersionList]:
        return cast(ApiResult[VersionList], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'versions', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def org_versions_api_v1_organizations__organization_id__consents__consent_id__versions_get_iterate(self, *, organization_id: str, consent_id: str, query: OrgVersionsApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsGetQuery | None = None, identity: Callable[[VersionResource], str | int]) -> AsyncIterator[VersionResource]:
        return self._transport.iterate('' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'versions', cast(Mapping[str, QueryValue], query), identity=identity)

    async def org_publish_api_v1_organizations__organization_id__consents__consent_id__versions_post(self, *, organization_id: str, consent_id: str, options: OrgPublishApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsPostWriteOptions, body: MultipartInput) -> ApiResult[VersionResource]:
        return cast(ApiResult[VersionResource], await self._transport.request('POST', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'versions', body, options or WriteOptions(), None))

    async def org_version_api_v1_organizations__organization_id__consents__consent_id__versions__version__get(self, *, organization_id: str, consent_id: str, version: int, options: WriteOptions | None = None) -> ApiResult[VersionResource]:
        return cast(ApiResult[VersionResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'consents' + '/' + quote(str(consent_id), safe='') + '/' + 'versions' + '/' + quote(str(version), safe=''), None, options or WriteOptions(), None))

    async def list_organization_domains_api_v1_organizations__organization_id__domains_get(self, *, organization_id: str, query: ListOrganizationDomainsApiV1OrganizationsOrganizationIdDomainsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[DomainList]:
        return cast(ApiResult[DomainList], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'domains', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_organization_domains_api_v1_organizations__organization_id__domains_get_iterate(self, *, organization_id: str, query: ListOrganizationDomainsApiV1OrganizationsOrganizationIdDomainsGetQuery | None = None, identity: Callable[[DomainResource], str | int] | None = None) -> AsyncIterator[DomainResource]:
        return self._transport.iterate('' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'domains', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_organization_domain_api_v1_organizations__organization_id__domains_post(self, *, organization_id: str, options: CreateOrganizationDomainApiV1OrganizationsOrganizationIdDomainsPostWriteOptions, body: DomainCreate) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('POST', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'domains', body, options or WriteOptions(), None))

    async def delete_organization_domain_api_v1_organizations__organization_id__domains__domain_id__delete(self, *, domain_id: str, organization_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'domains' + '/' + quote(str(domain_id), safe=''), None, options or WriteOptions(), None))

    async def get_organization_domain_api_v1_organizations__organization_id__domains__domain_id__get(self, *, domain_id: str, organization_id: str, options: WriteOptions | None = None) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'domains' + '/' + quote(str(domain_id), safe=''), None, options or WriteOptions(), None))

    async def patch_organization_domain_api_v1_organizations__organization_id__domains__domain_id__patch(self, *, organization_id: str, domain_id: str, options: WriteOptions | None = None, body: AccountDomainPatch | DelegatedDomainPatch) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('PATCH', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'domains' + '/' + quote(str(domain_id), safe=''), body, options or WriteOptions(), None))

    async def verify_organization_domain_api_v1_organizations__organization_id__domains__domain_id__verify_post(self, *, domain_id: str, organization_id: str, options: VerifyOrganizationDomainApiV1OrganizationsOrganizationIdDomainsDomainIdVerifyPostWriteOptions, body: Empty) -> ApiResult[DomainResource]:
        return cast(ApiResult[DomainResource], await self._transport.request('POST', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'domains' + '/' + quote(str(domain_id), safe='') + '/' + 'verify', body, options or WriteOptions(), None))

    async def list_memberships_api_v1_organizations__organization_id__memberships_get(self, *, organization_id: str, query: ListMembershipsApiV1OrganizationsOrganizationIdMembershipsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[MembershipList]:
        return cast(ApiResult[MembershipList], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'memberships', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_memberships_api_v1_organizations__organization_id__memberships_get_iterate(self, *, organization_id: str, query: ListMembershipsApiV1OrganizationsOrganizationIdMembershipsGetQuery | None = None, identity: Callable[[MembershipResource], str | int]) -> AsyncIterator[MembershipResource]:
        return self._transport.iterate('' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'memberships', cast(Mapping[str, QueryValue], query), identity=identity)

    async def create_membership_api_v1_organizations__organization_id__memberships_post(self, *, organization_id: str, options: CreateMembershipApiV1OrganizationsOrganizationIdMembershipsPostWriteOptions, body: MembershipCreate) -> ApiResult[MembershipResource]:
        return cast(ApiResult[MembershipResource], await self._transport.request('POST', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'memberships', body, options or WriteOptions(), None))

    async def delete_membership_api_v1_organizations__organization_id__memberships__user_id__delete(self, *, organization_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'memberships' + '/' + quote(str(user_id), safe=''), None, options or WriteOptions(), None))

    async def get_membership_api_v1_organizations__organization_id__memberships__user_id__get(self, *, organization_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[MembershipResource]:
        return cast(ApiResult[MembershipResource], await self._transport.request('GET', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'memberships' + '/' + quote(str(user_id), safe=''), None, options or WriteOptions(), None))

    async def patch_membership_api_v1_organizations__organization_id__memberships__user_id__patch(self, *, organization_id: str, user_id: str, options: WriteOptions | None = None, body: MembershipPatch) -> ApiResult[MembershipResource]:
        return cast(ApiResult[MembershipResource], await self._transport.request('PATCH', '' + '/' + 'organizations' + '/' + quote(str(organization_id), safe='') + '/' + 'memberships' + '/' + quote(str(user_id), safe=''), body, options or WriteOptions(), None))

    async def get_keys_api_v1_signing_keys_get(self, *, query: GetKeysApiV1SigningKeysGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[SigningKeyList]:
        return cast(ApiResult[SigningKeyList], await self._transport.request('GET', '' + '/' + 'signing-keys', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def get_keys_api_v1_signing_keys_get_iterate(self, *, query: GetKeysApiV1SigningKeysGetQuery | None = None, identity: Callable[[SigningKeyResource], str | int] | None = None) -> AsyncIterator[SigningKeyResource]:
        return self._transport.iterate('' + '/' + 'signing-keys', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def request_step_up_api_v1_step_up_post(self, *, options: WriteOptions | None = None, body: StepUpRequest) -> ApiResult[dict[str, Any]]:
        return cast(ApiResult[dict[str, Any]], await self._transport.request('POST', '' + '/' + 'step-up', body, options or WriteOptions(), None))

    async def remove_account_api_v1_support_delete(self, *, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'support', None, options or WriteOptions(), None))

    async def read_account_api_v1_support_get(self, *, options: WriteOptions | None = None) -> ApiResult[SupportResource]:
        return cast(ApiResult[SupportResource], await self._transport.request('GET', '' + '/' + 'support', None, options or WriteOptions(), None))

    async def patch_account_api_v1_support_patch(self, *, options: WriteOptions | None = None, body: SupportPatch) -> ApiResult[SupportResource]:
        return cast(ApiResult[SupportResource], await self._transport.request('PATCH', '' + '/' + 'support', body, options or WriteOptions(), None))

    async def verification_account_api_v1_support_verification_post(self, *, options: VerificationAccountApiV1SupportVerificationPostWriteOptions, body: EmptyRequest) -> ApiResult[VerificationQueued]:
        return cast(ApiResult[VerificationQueued], await self._transport.request('POST', '' + '/' + 'support' + '/' + 'verification', body, options or WriteOptions(), None))

    async def list_users_api_v1_users_get(self, *, query: ListUsersApiV1UsersGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[UserList]:
        return cast(ApiResult[UserList], await self._transport.request('GET', '' + '/' + 'users', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_users_api_v1_users_get_iterate(self, *, query: ListUsersApiV1UsersGetQuery | None = None, identity: Callable[[UserResource], str | int] | None = None) -> AsyncIterator[UserResource]:
        return self._transport.iterate('' + '/' + 'users', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_user_api_v1_users_post(self, *, options: CreateUserApiV1UsersPostWriteOptions, body: UserCreate) -> ApiResult[UserResource]:
        return cast(ApiResult[UserResource], await self._transport.request('POST', '' + '/' + 'users', body, options or WriteOptions(), None))

    async def delete_user_api_v1_users__user_id__delete(self, *, user_id: str, options: DeleteUserApiV1UsersUserIdDeleteWriteOptions) -> ApiResult[UserDeletionResult]:
        return cast(ApiResult[UserDeletionResult], await self._transport.request('DELETE', '' + '/' + 'users' + '/' + quote(str(user_id), safe=''), None, options or WriteOptions(), None))

    async def get_user_api_v1_users__user_id__get(self, *, user_id: str, options: WriteOptions | None = None) -> ApiResult[UserResource]:
        return cast(ApiResult[UserResource], await self._transport.request('GET', '' + '/' + 'users' + '/' + quote(str(user_id), safe=''), None, options or WriteOptions(), None))

    async def patch_user_api_v1_users__user_id__patch(self, *, user_id: str, options: WriteOptions | None = None, body: UserPatch) -> ApiResult[UserResource]:
        return cast(ApiResult[UserResource], await self._transport.request('PATCH', '' + '/' + 'users' + '/' + quote(str(user_id), safe=''), body, options or WriteOptions(), None))

    async def approve_user_api_v1_users__user_id__approve_post(self, *, user_id: str, options: ApproveUserApiV1UsersUserIdApprovePostWriteOptions) -> ApiResult[UserResource]:
        return cast(ApiResult[UserResource], await self._transport.request('POST', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'approve', None, options or WriteOptions(), None))

    async def export_user_api_v1_users__user_id__export_get(self, *, user_id: str, options: WriteOptions | None = None) -> ApiResult[Any]:
        return cast(ApiResult[Any], await self._transport.request('GET', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'export', None, options or WriteOptions(), None))

    async def list_user_memberships_api_v1_users__user_id__memberships_get(self, *, user_id: str, query: ListUserMembershipsApiV1UsersUserIdMembershipsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[MembershipList]:
        return cast(ApiResult[MembershipList], await self._transport.request('GET', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'memberships', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_user_memberships_api_v1_users__user_id__memberships_get_iterate(self, *, user_id: str, query: ListUserMembershipsApiV1UsersUserIdMembershipsGetQuery | None = None, identity: Callable[[MembershipResource], str | int]) -> AsyncIterator[MembershipResource]:
        return self._transport.iterate('' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'memberships', cast(Mapping[str, QueryValue], query), identity=identity)

    async def reset_mfa_api_v1_users__user_id__mfa_reset_post(self, *, user_id: str, options: ResetMfaApiV1UsersUserIdMfaResetPostWriteOptions) -> ApiResult[MfaResetResult]:
        return cast(ApiResult[MfaResetResult], await self._transport.request('POST', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'mfa' + '/' + 'reset', None, options or WriteOptions(), None))

    async def unblock_processing_api_v1_users__user_id__processing_block_delete(self, *, user_id: str, options: UnblockProcessingApiV1UsersUserIdProcessingBlockDeleteWriteOptions) -> ApiResult[UserResource]:
        return cast(ApiResult[UserResource], await self._transport.request('DELETE', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'processing-block', None, options or WriteOptions(), None))

    async def block_processing_api_v1_users__user_id__processing_block_post(self, *, user_id: str, options: BlockProcessingApiV1UsersUserIdProcessingBlockPostWriteOptions) -> ApiResult[UserResource]:
        return cast(ApiResult[UserResource], await self._transport.request('POST', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'processing-block', None, options or WriteOptions(), None))

    async def issue_recovery_api_v1_users__user_id__recovery_post(self, *, user_id: str, options: IssueRecoveryApiV1UsersUserIdRecoveryPostWriteOptions) -> ApiResult[RecoveryResult]:
        return cast(ApiResult[RecoveryResult], await self._transport.request('POST', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'recovery', None, options or WriteOptions(), None))

    async def reject_user_api_v1_users__user_id__reject_post(self, *, user_id: str, options: RejectUserApiV1UsersUserIdRejectPostWriteOptions) -> ApiResult[UserDeletionResult]:
        return cast(ApiResult[UserDeletionResult], await self._transport.request('POST', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'reject', None, options or WriteOptions(), None))

    async def list_sessions_api_v1_users__user_id__sessions_get(self, *, user_id: str, query: ListSessionsApiV1UsersUserIdSessionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[SessionList]:
        return cast(ApiResult[SessionList], await self._transport.request('GET', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'sessions', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_sessions_api_v1_users__user_id__sessions_get_iterate(self, *, user_id: str, query: ListSessionsApiV1UsersUserIdSessionsGetQuery | None = None, identity: Callable[[SessionResource], str | int] | None = None) -> AsyncIterator[SessionResource]:
        return self._transport.iterate('' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'sessions', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def revoke_user_sessions_api_v1_users__user_id__sessions_revoke_post(self, *, user_id: str, options: RevokeUserSessionsApiV1UsersUserIdSessionsRevokePostWriteOptions) -> ApiResult[UserRevocationResult]:
        return cast(ApiResult[UserRevocationResult], await self._transport.request('POST', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'sessions' + '/' + 'revoke', None, options or WriteOptions(), None))

    async def delete_session_api_v1_users__user_id__sessions__session_id__delete(self, *, user_id: str, session_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'sessions' + '/' + quote(str(session_id), safe=''), None, options or WriteOptions(), None))

    async def get_session_api_v1_users__user_id__sessions__session_id__get(self, *, user_id: str, session_id: str, options: WriteOptions | None = None) -> ApiResult[SessionResource]:
        return cast(ApiResult[SessionResource], await self._transport.request('GET', '' + '/' + 'users' + '/' + quote(str(user_id), safe='') + '/' + 'sessions' + '/' + quote(str(session_id), safe=''), None, options or WriteOptions(), None))

    async def list_deliveries_api_v1_webhook_deliveries_get(self, *, query: ListDeliveriesApiV1WebhookDeliveriesGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[DeliveryList]:
        return cast(ApiResult[DeliveryList], await self._transport.request('GET', '' + '/' + 'webhook-deliveries', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_deliveries_api_v1_webhook_deliveries_get_iterate(self, *, query: ListDeliveriesApiV1WebhookDeliveriesGetQuery | None = None, identity: Callable[[DeliveryResource], str | int] | None = None) -> AsyncIterator[DeliveryResource]:
        return self._transport.iterate('' + '/' + 'webhook-deliveries', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def get_delivery_api_v1_webhook_deliveries__delivery_id__get(self, *, delivery_id: str, options: WriteOptions | None = None) -> ApiResult[DeliveryResource]:
        return cast(ApiResult[DeliveryResource], await self._transport.request('GET', '' + '/' + 'webhook-deliveries' + '/' + quote(str(delivery_id), safe=''), None, options or WriteOptions(), None))

    async def retry_delivery_api_v1_webhook_deliveries__delivery_id__retry_post(self, *, delivery_id: str, options: RetryDeliveryApiV1WebhookDeliveriesDeliveryIdRetryPostWriteOptions, body: Empty) -> ApiResult[DeliveryResource]:
        return cast(ApiResult[DeliveryResource], await self._transport.request('POST', '' + '/' + 'webhook-deliveries' + '/' + quote(str(delivery_id), safe='') + '/' + 'retry', body, options or WriteOptions(), None))

    async def list_endpoints_api_v1_webhook_endpoints_get(self, *, query: ListEndpointsApiV1WebhookEndpointsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[EndpointList]:
        return cast(ApiResult[EndpointList], await self._transport.request('GET', '' + '/' + 'webhook-endpoints', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def list_endpoints_api_v1_webhook_endpoints_get_iterate(self, *, query: ListEndpointsApiV1WebhookEndpointsGetQuery | None = None, identity: Callable[[EndpointResource], str | int] | None = None) -> AsyncIterator[EndpointResource]:
        return self._transport.iterate('' + '/' + 'webhook-endpoints', cast(Mapping[str, QueryValue], query), identity=identity or (lambda item: cast(str | int, item['id'])))

    async def create_endpoint_api_v1_webhook_endpoints_post(self, *, options: CreateEndpointApiV1WebhookEndpointsPostWriteOptions, body: EndpointCreate) -> ApiResult[EndpointResource]:
        return cast(ApiResult[EndpointResource], await self._transport.request('POST', '' + '/' + 'webhook-endpoints', body, options or WriteOptions(), None))

    async def delete_endpoint_api_v1_webhook_endpoints__endpoint_id__delete(self, *, endpoint_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return cast(ApiResult[None], await self._transport.request('DELETE', '' + '/' + 'webhook-endpoints' + '/' + quote(str(endpoint_id), safe=''), None, options or WriteOptions(), None))

    async def get_endpoint_api_v1_webhook_endpoints__endpoint_id__get(self, *, endpoint_id: str, options: WriteOptions | None = None) -> ApiResult[EndpointResource]:
        return cast(ApiResult[EndpointResource], await self._transport.request('GET', '' + '/' + 'webhook-endpoints' + '/' + quote(str(endpoint_id), safe=''), None, options or WriteOptions(), None))

    async def patch_endpoint_api_v1_webhook_endpoints__endpoint_id__patch(self, *, endpoint_id: str, options: WriteOptions | None = None, body: EndpointPatch) -> ApiResult[EndpointResource]:
        return cast(ApiResult[EndpointResource], await self._transport.request('PATCH', '' + '/' + 'webhook-endpoints' + '/' + quote(str(endpoint_id), safe=''), body, options or WriteOptions(), None))

    async def change_destination_api_v1_webhook_endpoints__endpoint_id__destination_changes_post(self, *, endpoint_id: str, options: ChangeDestinationApiV1WebhookEndpointsEndpointIdDestinationChangesPostWriteOptions, body: DestinationChange) -> ApiResult[StwrdIdpAdminApiWebhookEndpointsRotationResource]:
        return cast(ApiResult[StwrdIdpAdminApiWebhookEndpointsRotationResource], await self._transport.request('POST', '' + '/' + 'webhook-endpoints' + '/' + quote(str(endpoint_id), safe='') + '/' + 'destination-changes', body, options or WriteOptions(), None))

    async def rotate_endpoint_api_v1_webhook_endpoints__endpoint_id__secret_rotations_post(self, *, endpoint_id: str, options: RotateEndpointApiV1WebhookEndpointsEndpointIdSecretRotationsPostWriteOptions, body: RotationCreate) -> ApiResult[StwrdIdpAdminApiWebhookEndpointsRotationResource]:
        return cast(ApiResult[StwrdIdpAdminApiWebhookEndpointsRotationResource], await self._transport.request('POST', '' + '/' + 'webhook-endpoints' + '/' + quote(str(endpoint_id), safe='') + '/' + 'secret-rotations', body, options or WriteOptions(), None))

    async def reveal_endpoint_api_v1_webhook_endpoints__endpoint_id__secret_reveal_post(self, *, endpoint_id: str, options: WriteOptions | None = None, body: Empty) -> ApiResult[StwrdIdpAdminApiWebhookEndpointsSecretResource]:
        return cast(ApiResult[StwrdIdpAdminApiWebhookEndpointsSecretResource], await self._transport.request('POST', '' + '/' + 'webhook-endpoints' + '/' + quote(str(endpoint_id), safe='') + '/' + 'secret' + '/' + 'reveal', body, options or WriteOptions(), None))

    async def test_endpoint_api_v1_webhook_endpoints__endpoint_id__test_post(self, *, endpoint_id: str, options: TestEndpointApiV1WebhookEndpointsEndpointIdTestPostWriteOptions, body: Empty) -> ApiResult[TestResource]:
        return cast(ApiResult[TestResource], await self._transport.request('POST', '' + '/' + 'webhook-endpoints' + '/' + quote(str(endpoint_id), safe='') + '/' + 'test', body, options or WriteOptions(), None))

    async def event_types_api_v1_webhook_event_types_get(self, *, query: EventTypesApiV1WebhookEventTypesGetQuery, options: WriteOptions | None = None) -> ApiResult[EventTypeList]:
        return cast(ApiResult[EventTypeList], await self._transport.request('GET', '' + '/' + 'webhook-event-types', None, options or WriteOptions(), cast(Mapping[str, QueryValue], query) if query is not None else None))

    def event_types_api_v1_webhook_event_types_get_iterate(self, *, query: EventTypesApiV1WebhookEventTypesGetQuery, identity: Callable[[EventTypeResource], str | int]) -> AsyncIterator[EventTypeResource]:
        return self._transport.iterate('' + '/' + 'webhook-event-types', cast(Mapping[str, QueryValue], query), identity=identity)

class ResourceApplicationsAuthenticationEntry:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[EntryResource]:
        return await self._operations.get_entry_api_v1_applications__application_id__authentication_entry_get(application_id=application_id, options=options)
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: EntryPatch) -> ApiResult[EntryResource]:
        return await self._operations.patch_entry_api_v1_applications__application_id__authentication_entry_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsBrandingAssets:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, application_id: str, options: AssetsApplicationApiV1ApplicationsApplicationIdBrandingAssetsPostWriteOptions, body: MultipartInput) -> ApiResult[AssetResource]:
        return await self._operations.assets_application_api_v1_applications__application_id__branding_assets_post(application_id=application_id, options=options, body=body)

class ResourceApplicationsBrandingLanguage:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: LanguagePatch) -> ApiResult[BrandingResource]:
        return await self._operations.language_application_api_v1_applications__application_id__branding_language_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsBrandingLoginPreview:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, application_id: str, options: WriteOptions | None = None, body: PreviewRequest) -> ApiResult[PreviewResponse]:
        return await self._operations.login_preview_application_api_v1_applications__application_id__branding_login_preview_post(application_id=application_id, options=options, body=body)

class ResourceApplicationsBrandingSeal:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: SealPatch) -> ApiResult[BrandingResource]:
        return await self._operations.seal_application_api_v1_applications__application_id__branding_seal_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsChannelsIdentity:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def update(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: WriteOptions | None = None, body: EmailIdentity | WhatsappIdentity) -> ApiResult[ChannelResource]:
        return await self._operations.identity_application_api_v1_applications__application_id__channels__channel_type__identity_patch(channel_type=channel_type, application_id=application_id, options=options, body=body)

class ResourceApplicationsChannelsTest:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: TestApplicationApiV1ApplicationsApplicationIdChannelsChannelTypeTestPostWriteOptions, body: Empty | PhoneStart | PhoneConfirm) -> ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult]:
        return await self._operations.test_application_api_v1_applications__application_id__channels__channel_type__test_post(channel_type=channel_type, application_id=application_id, options=options, body=body)

class ResourceApplicationsChannelsVerify:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: VerifyApplicationApiV1ApplicationsApplicationIdChannelsChannelTypeVerifyPostWriteOptions, body: Empty) -> ApiResult[ChannelResource]:
        return await self._operations.verify_application_api_v1_applications__application_id__channels__channel_type__verify_post(channel_type=channel_type, application_id=application_id, options=options, body=body)

class ResourceApplicationsConsentsImpact:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, application_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[ImpactResource]:
        return await self._operations.app_impact_api_v1_applications__application_id__consents__consent_id__impact_get(application_id=application_id, consent_id=consent_id, options=options)

class ResourceApplicationsConsentsVersions:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, application_id: str, consent_id: str, query: AppVersionsApiV1ApplicationsApplicationIdConsentsConsentIdVersionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[VersionList]:
        return await self._operations.app_versions_api_v1_applications__application_id__consents__consent_id__versions_get(application_id=application_id, consent_id=consent_id, query=query, options=options)
    def iterate(self, *, application_id: str, consent_id: str, query: AppVersionsApiV1ApplicationsApplicationIdConsentsConsentIdVersionsGetQuery | None = None, identity: Callable[[VersionResource], str | int]) -> AsyncIterator[VersionResource]:
        return self._operations.app_versions_api_v1_applications__application_id__consents__consent_id__versions_get_iterate(application_id=application_id, consent_id=consent_id, query=query, identity=identity)
    async def create(self, *, application_id: str, consent_id: str, options: AppPublishApiV1ApplicationsApplicationIdConsentsConsentIdVersionsPostWriteOptions, body: MultipartInput) -> ApiResult[VersionResource]:
        return await self._operations.app_publish_api_v1_applications__application_id__consents__consent_id__versions_post(application_id=application_id, consent_id=consent_id, options=options, body=body)
    async def get(self, *, application_id: str, consent_id: str, version: int, options: WriteOptions | None = None) -> ApiResult[VersionResource]:
        return await self._operations.app_version_api_v1_applications__application_id__consents__consent_id__versions__version__get(application_id=application_id, consent_id=consent_id, version=version, options=options)

class ResourceApplicationsDomainsActivate:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, application_id: str, domain_id: str, options: ActivateApplicationDomainApiV1ApplicationsApplicationIdDomainsDomainIdActivatePostWriteOptions, body: Empty) -> ApiResult[DomainResource]:
        return await self._operations.activate_application_domain_api_v1_applications__application_id__domains__domain_id__activate_post(application_id=application_id, domain_id=domain_id, options=options, body=body)

class ResourceApplicationsDomainsVerify:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, domain_id: str, application_id: str, options: VerifyApplicationDomainApiV1ApplicationsApplicationIdDomainsDomainIdVerifyPostWriteOptions, body: Empty) -> ApiResult[DomainResource]:
        return await self._operations.verify_application_domain_api_v1_applications__application_id__domains__domain_id__verify_post(domain_id=domain_id, application_id=application_id, options=options, body=body)

class ResourceApplicationsSecretReveal:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[StwrdIdpAdminApplicationConfigurationSecretResource]:
        return await self._operations.reveal_secret_api_v1_applications__application_id__secret_reveal_post(application_id=application_id, options=options)

class ResourceApplicationsSupportVerification:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, application_id: str, options: VerificationApplicationApiV1ApplicationsApplicationIdSupportVerificationPostWriteOptions, body: EmptyRequest) -> ApiResult[VerificationQueued]:
        return await self._operations.verification_application_api_v1_applications__application_id__support_verification_post(application_id=application_id, options=options, body=body)

class ResourceApplicationsUsersRoles:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def delete(self, *, application_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_user_roles_api_v1_applications__application_id__users__user_id__roles_delete(application_id=application_id, user_id=user_id, options=options)
    async def get(self, *, application_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[AssignedAccess]:
        return await self._operations.get_user_roles_api_v1_applications__application_id__users__user_id__roles_get(application_id=application_id, user_id=user_id, options=options)
    async def replace(self, *, application_id: str, user_id: str, options: WriteOptions | None = None, body: RolesPut) -> ApiResult[AssignedAccess]:
        return await self._operations.put_user_roles_api_v1_applications__application_id__users__user_id__roles_put(application_id=application_id, user_id=user_id, options=options, body=body)

class ResourceOrganizationsApplicationsMembers:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def delete(self, *, organization_id: str, application_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_member_access_api_v1_organizations__organization_id__applications__application_id__members__user_id__delete(organization_id=organization_id, application_id=application_id, user_id=user_id, options=options)
    async def get(self, *, organization_id: str, application_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[AssignedAccess]:
        return await self._operations.get_member_access_api_v1_organizations__organization_id__applications__application_id__members__user_id__get(organization_id=organization_id, application_id=application_id, user_id=user_id, options=options)
    async def replace(self, *, organization_id: str, application_id: str, user_id: str, options: WriteOptions | None = None, body: RolesPut) -> ApiResult[AssignedAccess]:
        return await self._operations.put_member_access_api_v1_organizations__organization_id__applications__application_id__members__user_id__put(organization_id=organization_id, application_id=application_id, user_id=user_id, options=options, body=body)

class ResourceOrganizationsApplicationsRoles:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, organization_id: str, application_id: str, query: ListOrganizationApplicationRolesApiV1OrganizationsOrganizationIdApplicationsApplicationIdRolesGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[RoleList]:
        return await self._operations.list_organization_application_roles_api_v1_organizations__organization_id__applications__application_id__roles_get(organization_id=organization_id, application_id=application_id, query=query, options=options)
    def iterate(self, *, organization_id: str, application_id: str, query: ListOrganizationApplicationRolesApiV1OrganizationsOrganizationIdApplicationsApplicationIdRolesGetQuery | None = None, identity: Callable[[RoleResource], str | int] | None = None) -> AsyncIterator[RoleResource]:
        return self._operations.list_organization_application_roles_api_v1_organizations__organization_id__applications__application_id__roles_get_iterate(organization_id=organization_id, application_id=application_id, query=query, identity=identity)

class ResourceOrganizationsChannelsIdentity:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def update(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: WriteOptions | None = None, body: EmailIdentity | WhatsappIdentity) -> ApiResult[ChannelResource]:
        return await self._operations.identity_organization_api_v1_organizations__organization_id__channels__channel_type__identity_patch(channel_type=channel_type, organization_id=organization_id, options=options, body=body)

class ResourceOrganizationsChannelsTest:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: TestOrganizationApiV1OrganizationsOrganizationIdChannelsChannelTypeTestPostWriteOptions, body: Empty | PhoneStart | PhoneConfirm) -> ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult]:
        return await self._operations.test_organization_api_v1_organizations__organization_id__channels__channel_type__test_post(channel_type=channel_type, organization_id=organization_id, options=options, body=body)

class ResourceOrganizationsChannelsVerify:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: VerifyOrganizationApiV1OrganizationsOrganizationIdChannelsChannelTypeVerifyPostWriteOptions, body: Empty) -> ApiResult[ChannelResource]:
        return await self._operations.verify_organization_api_v1_organizations__organization_id__channels__channel_type__verify_post(channel_type=channel_type, organization_id=organization_id, options=options, body=body)

class ResourceOrganizationsConsentsImpact:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, organization_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[ImpactResource]:
        return await self._operations.org_impact_api_v1_organizations__organization_id__consents__consent_id__impact_get(organization_id=organization_id, consent_id=consent_id, options=options)

class ResourceOrganizationsConsentsVersions:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, organization_id: str, consent_id: str, query: OrgVersionsApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[VersionList]:
        return await self._operations.org_versions_api_v1_organizations__organization_id__consents__consent_id__versions_get(organization_id=organization_id, consent_id=consent_id, query=query, options=options)
    def iterate(self, *, organization_id: str, consent_id: str, query: OrgVersionsApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsGetQuery | None = None, identity: Callable[[VersionResource], str | int]) -> AsyncIterator[VersionResource]:
        return self._operations.org_versions_api_v1_organizations__organization_id__consents__consent_id__versions_get_iterate(organization_id=organization_id, consent_id=consent_id, query=query, identity=identity)
    async def create(self, *, organization_id: str, consent_id: str, options: OrgPublishApiV1OrganizationsOrganizationIdConsentsConsentIdVersionsPostWriteOptions, body: MultipartInput) -> ApiResult[VersionResource]:
        return await self._operations.org_publish_api_v1_organizations__organization_id__consents__consent_id__versions_post(organization_id=organization_id, consent_id=consent_id, options=options, body=body)
    async def get(self, *, organization_id: str, consent_id: str, version: int, options: WriteOptions | None = None) -> ApiResult[VersionResource]:
        return await self._operations.org_version_api_v1_organizations__organization_id__consents__consent_id__versions__version__get(organization_id=organization_id, consent_id=consent_id, version=version, options=options)

class ResourceOrganizationsDomainsVerify:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, domain_id: str, organization_id: str, options: VerifyOrganizationDomainApiV1OrganizationsOrganizationIdDomainsDomainIdVerifyPostWriteOptions, body: Empty) -> ApiResult[DomainResource]:
        return await self._operations.verify_organization_domain_api_v1_organizations__organization_id__domains__domain_id__verify_post(domain_id=domain_id, organization_id=organization_id, options=options, body=body)

class ResourceUsersMfaReset:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, user_id: str, options: ResetMfaApiV1UsersUserIdMfaResetPostWriteOptions) -> ApiResult[MfaResetResult]:
        return await self._operations.reset_mfa_api_v1_users__user_id__mfa_reset_post(user_id=user_id, options=options)

class ResourceUsersSessionsRevoke:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, user_id: str, options: RevokeUserSessionsApiV1UsersUserIdSessionsRevokePostWriteOptions) -> ApiResult[UserRevocationResult]:
        return await self._operations.revoke_user_sessions_api_v1_users__user_id__sessions_revoke_post(user_id=user_id, options=options)

class ResourceWebhookEndpointsSecretReveal:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, endpoint_id: str, options: WriteOptions | None = None, body: Empty) -> ApiResult[StwrdIdpAdminApiWebhookEndpointsSecretResource]:
        return await self._operations.reveal_endpoint_api_v1_webhook_endpoints__endpoint_id__secret_reveal_post(endpoint_id=endpoint_id, options=options, body=body)

class ResourceApplicationsAgentInstructions:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, application_id: str, query: GetAgentInstructionsApiV1ApplicationsApplicationIdAgentInstructionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[AgentInstructionsResource]:
        return await self._operations.get_agent_instructions_api_v1_applications__application_id__agent_instructions_get(application_id=application_id, query=query, options=options)

class ResourceApplicationsAuthentication:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.entry = ResourceApplicationsAuthenticationEntry(operations)
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[AuthenticationResource]:
        return await self._operations.get_authentication_api_v1_applications__application_id__authentication_get(application_id=application_id, options=options)
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: AuthenticationPatch) -> ApiResult[AuthenticationResource]:
        return await self._operations.patch_authentication_api_v1_applications__application_id__authentication_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsBranding:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.assets = ResourceApplicationsBrandingAssets(operations)
        self.language = ResourceApplicationsBrandingLanguage(operations)
        self.login_preview = ResourceApplicationsBrandingLoginPreview(operations)
        self.seal = ResourceApplicationsBrandingSeal(operations)
    async def delete(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.remove_application_api_v1_applications__application_id__branding_delete(application_id=application_id, options=options)
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[BrandingResource]:
        return await self._operations.read_application_api_v1_applications__application_id__branding_get(application_id=application_id, options=options)
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: Theme) -> ApiResult[BrandingResource]:
        return await self._operations.patch_application_api_v1_applications__application_id__branding_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsChannels:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.identity = ResourceApplicationsChannelsIdentity(operations)
        self.test = ResourceApplicationsChannelsTest(operations)
        self.verify = ResourceApplicationsChannelsVerify(operations)
    async def list(self, *, application_id: str, query: ListApplicationApiV1ApplicationsApplicationIdChannelsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ChannelList]:
        return await self._operations.list_application_api_v1_applications__application_id__channels_get(application_id=application_id, query=query, options=options)
    def iterate(self, *, application_id: str, query: ListApplicationApiV1ApplicationsApplicationIdChannelsGetQuery | None = None, identity: Callable[[ChannelResource], str | int]) -> AsyncIterator[ChannelResource]:
        return self._operations.list_application_api_v1_applications__application_id__channels_get_iterate(application_id=application_id, query=query, identity=identity)
    async def delete(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.remove_application_api_v1_applications__application_id__channels__channel_type__delete(channel_type=channel_type, application_id=application_id, options=options)
    async def get(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: WriteOptions | None = None) -> ApiResult[ChannelResource]:
        return await self._operations.read_application_api_v1_applications__application_id__channels__channel_type__get(channel_type=channel_type, application_id=application_id, options=options)
    async def update(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], application_id: str, options: WriteOptions | None = None, body: ChannelPatch) -> ApiResult[ChannelResource]:
        return await self._operations.patch_application_api_v1_applications__application_id__channels__channel_type__patch(channel_type=channel_type, application_id=application_id, options=options, body=body)

class ResourceApplicationsClaims:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[ClaimsResource]:
        return await self._operations.get_claims_api_v1_applications__application_id__claims_get(application_id=application_id, options=options)
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: ClaimsPut) -> ApiResult[ClaimsResource]:
        return await self._operations.patch_claims_api_v1_applications__application_id__claims_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsConsentReceipt:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[ReceiptResource]:
        return await self._operations.get_receipt_api_v1_applications__application_id__consent_receipt_get(application_id=application_id, options=options)
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: ReceiptPatch) -> ApiResult[ReceiptResource]:
        return await self._operations.patch_receipt_api_v1_applications__application_id__consent_receipt_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsConsents:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.impact = ResourceApplicationsConsentsImpact(operations)
        self.versions = ResourceApplicationsConsentsVersions(operations)
    async def list(self, *, application_id: str, query: AppListApiV1ApplicationsApplicationIdConsentsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[TermList]:
        return await self._operations.app_list_api_v1_applications__application_id__consents_get(application_id=application_id, query=query, options=options)
    def iterate(self, *, application_id: str, query: AppListApiV1ApplicationsApplicationIdConsentsGetQuery | None = None, identity: Callable[[TermResource], str | int] | None = None) -> AsyncIterator[TermResource]:
        return self._operations.app_list_api_v1_applications__application_id__consents_get_iterate(application_id=application_id, query=query, identity=identity)
    async def create(self, *, application_id: str, options: AppCreateApiV1ApplicationsApplicationIdConsentsPostWriteOptions, body: TermCreate) -> ApiResult[TermResource]:
        return await self._operations.app_create_api_v1_applications__application_id__consents_post(application_id=application_id, options=options, body=body)
    async def delete(self, *, application_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.app_retire_api_v1_applications__application_id__consents__consent_id__delete(application_id=application_id, consent_id=consent_id, options=options)
    async def get(self, *, application_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[TermResource]:
        return await self._operations.app_read_api_v1_applications__application_id__consents__consent_id__get(application_id=application_id, consent_id=consent_id, options=options)
    async def update(self, *, application_id: str, consent_id: str, options: WriteOptions | None = None, body: TermPatch) -> ApiResult[TermMutationResponse]:
        return await self._operations.app_patch_api_v1_applications__application_id__consents__consent_id__patch(application_id=application_id, consent_id=consent_id, options=options, body=body)

class ResourceApplicationsDomains:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.activate = ResourceApplicationsDomainsActivate(operations)
        self.verify = ResourceApplicationsDomainsVerify(operations)
    async def list(self, *, application_id: str, query: ListApplicationDomainsApiV1ApplicationsApplicationIdDomainsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[DomainList]:
        return await self._operations.list_application_domains_api_v1_applications__application_id__domains_get(application_id=application_id, query=query, options=options)
    def iterate(self, *, application_id: str, query: ListApplicationDomainsApiV1ApplicationsApplicationIdDomainsGetQuery | None = None, identity: Callable[[DomainResource], str | int] | None = None) -> AsyncIterator[DomainResource]:
        return self._operations.list_application_domains_api_v1_applications__application_id__domains_get_iterate(application_id=application_id, query=query, identity=identity)
    async def create(self, *, application_id: str, options: CreateApplicationDomainApiV1ApplicationsApplicationIdDomainsPostWriteOptions, body: DomainCreate) -> ApiResult[DomainResource]:
        return await self._operations.create_application_domain_api_v1_applications__application_id__domains_post(application_id=application_id, options=options, body=body)
    async def delete(self, *, domain_id: str, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_application_domain_api_v1_applications__application_id__domains__domain_id__delete(domain_id=domain_id, application_id=application_id, options=options)
    async def get(self, *, domain_id: str, application_id: str, options: WriteOptions | None = None) -> ApiResult[DomainResource]:
        return await self._operations.get_application_domain_api_v1_applications__application_id__domains__domain_id__get(domain_id=domain_id, application_id=application_id, options=options)

class ResourceApplicationsPermissions:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, application_id: str, query: ListPermissionsApiV1ApplicationsApplicationIdPermissionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[PermissionList]:
        return await self._operations.list_permissions_api_v1_applications__application_id__permissions_get(application_id=application_id, query=query, options=options)
    def iterate(self, *, application_id: str, query: ListPermissionsApiV1ApplicationsApplicationIdPermissionsGetQuery | None = None, identity: Callable[[PermissionResource], str | int] | None = None) -> AsyncIterator[PermissionResource]:
        return self._operations.list_permissions_api_v1_applications__application_id__permissions_get_iterate(application_id=application_id, query=query, identity=identity)
    async def replace(self, *, application_id: str, options: WriteOptions | None = None, body: PermissionsPut) -> ApiResult[PermissionsResource]:
        return await self._operations.put_permissions_api_v1_applications__application_id__permissions_put(application_id=application_id, options=options, body=body)

class ResourceApplicationsRoles:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, application_id: str, query: ListRolesApiV1ApplicationsApplicationIdRolesGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[RoleList]:
        return await self._operations.list_roles_api_v1_applications__application_id__roles_get(application_id=application_id, query=query, options=options)
    def iterate(self, *, application_id: str, query: ListRolesApiV1ApplicationsApplicationIdRolesGetQuery | None = None, identity: Callable[[RoleResource], str | int] | None = None) -> AsyncIterator[RoleResource]:
        return self._operations.list_roles_api_v1_applications__application_id__roles_get_iterate(application_id=application_id, query=query, identity=identity)
    async def create(self, *, application_id: str, options: CreateRoleApiV1ApplicationsApplicationIdRolesPostWriteOptions, body: RoleCreate) -> ApiResult[RoleResource]:
        return await self._operations.create_role_api_v1_applications__application_id__roles_post(application_id=application_id, options=options, body=body)
    async def delete(self, *, application_id: str, role_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_role_api_v1_applications__application_id__roles__role_id__delete(application_id=application_id, role_id=role_id, options=options)
    async def get(self, *, application_id: str, role_id: str, options: WriteOptions | None = None) -> ApiResult[RoleResource]:
        return await self._operations.get_role_api_v1_applications__application_id__roles__role_id__get(application_id=application_id, role_id=role_id, options=options)
    async def update(self, *, application_id: str, role_id: str, options: WriteOptions | None = None, body: RolePatch) -> ApiResult[RoleResource]:
        return await self._operations.patch_role_api_v1_applications__application_id__roles__role_id__patch(application_id=application_id, role_id=role_id, options=options, body=body)

class ResourceApplicationsSecret:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.reveal = ResourceApplicationsSecretReveal(operations)

class ResourceApplicationsSecretRotations:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, application_id: str, options: RotateSecretApiV1ApplicationsApplicationIdSecretRotationsPostWriteOptions, body: RotationCreate) -> ApiResult[StwrdIdpAdminApplicationConfigurationRotationResource]:
        return await self._operations.rotate_secret_api_v1_applications__application_id__secret_rotations_post(application_id=application_id, options=options, body=body)

class ResourceApplicationsSupport:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.verification = ResourceApplicationsSupportVerification(operations)
    async def delete(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.remove_application_api_v1_applications__application_id__support_delete(application_id=application_id, options=options)
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[SupportResource]:
        return await self._operations.read_application_api_v1_applications__application_id__support_get(application_id=application_id, options=options)
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: SupportPatch) -> ApiResult[SupportResource]:
        return await self._operations.patch_application_api_v1_applications__application_id__support_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsTestLogin:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[TestLoginResource]:
        return await self._operations.get_test_login_api_v1_applications__application_id__test_login_get(application_id=application_id, options=options)

class ResourceApplicationsTokens:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[TokensResource]:
        return await self._operations.get_tokens_api_v1_applications__application_id__tokens_get(application_id=application_id, options=options)
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: TokensPatch) -> ApiResult[TokensResource]:
        return await self._operations.patch_tokens_api_v1_applications__application_id__tokens_patch(application_id=application_id, options=options, body=body)

class ResourceApplicationsUsers:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.roles = ResourceApplicationsUsersRoles(operations)

class ResourceBrandingAssets:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, options: AssetsAccountApiV1BrandingAssetsPostWriteOptions, body: MultipartInput) -> ApiResult[AssetResource]:
        return await self._operations.assets_account_api_v1_branding_assets_post(options=options, body=body)

class ResourceBrandingLoginPreview:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, options: WriteOptions | None = None, body: PreviewRequest) -> ApiResult[PreviewResponse]:
        return await self._operations.login_preview_account_api_v1_branding_login_preview_post(options=options, body=body)

class ResourceBrandingSeal:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def update(self, *, options: WriteOptions | None = None, body: SealPatch) -> ApiResult[BrandingResource]:
        return await self._operations.seal_account_api_v1_branding_seal_patch(options=options, body=body)

class ResourceChannelsIdentity:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def update(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: WriteOptions | None = None, body: EmailIdentity | WhatsappIdentity) -> ApiResult[ChannelResource]:
        return await self._operations.identity_account_api_v1_channels__channel_type__identity_patch(channel_type=channel_type, options=options, body=body)

class ResourceChannelsTest:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: TestAccountApiV1ChannelsChannelTypeTestPostWriteOptions, body: Empty | PhoneStart | PhoneConfirm) -> ApiResult[EmailTestResult | PhoneStartResult | PhoneConfirmResult]:
        return await self._operations.test_account_api_v1_channels__channel_type__test_post(channel_type=channel_type, options=options, body=body)

class ResourceChannelsVerify:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: VerifyAccountApiV1ChannelsChannelTypeVerifyPostWriteOptions, body: Empty) -> ApiResult[ChannelResource]:
        return await self._operations.verify_account_api_v1_channels__channel_type__verify_post(channel_type=channel_type, options=options, body=body)

class ResourceConsentActsRevoke:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, act_id: str, options: RevokeActApiV1ConsentActsActIdRevokePostWriteOptions, body: Empty) -> ApiResult[ActResource]:
        return await self._operations.revoke_act_api_v1_consent_acts__act_id__revoke_post(act_id=act_id, options=options, body=body)

class ResourceDomainsVerify:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, domain_id: str, options: VerifyAccountDomainApiV1DomainsDomainIdVerifyPostWriteOptions, body: Empty) -> ApiResult[DomainResource]:
        return await self._operations.verify_account_domain_api_v1_domains__domain_id__verify_post(domain_id=domain_id, options=options, body=body)

class ResourceInvitationsResend:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, invitation_id: str, options: ResendInvitationApiV1InvitationsInvitationIdResendPostWriteOptions) -> ApiResult[InvitationResource]:
        return await self._operations.resend_invitation_api_v1_invitations__invitation_id__resend_post(invitation_id=invitation_id, options=options)

class ResourceMeMemberships:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, query: SelfMembershipsApiV1MeMembershipsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[SelfMembershipList]:
        return await self._operations.self_memberships_api_v1_me_memberships_get(query=query, options=options)
    def iterate(self, *, query: SelfMembershipsApiV1MeMembershipsGetQuery | None = None, identity: Callable[[SelfMembership], str | int]) -> AsyncIterator[SelfMembership]:
        return self._operations.self_memberships_api_v1_me_memberships_get_iterate(query=query, identity=identity)

class ResourceOrganizationsApplications:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.members = ResourceOrganizationsApplicationsMembers(operations)
        self.roles = ResourceOrganizationsApplicationsRoles(operations)
    async def list(self, *, organization_id: str, query: ListEnabledApplicationsApiV1OrganizationsOrganizationIdApplicationsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[EnabledApplicationList]:
        return await self._operations.list_enabled_applications_api_v1_organizations__organization_id__applications_get(organization_id=organization_id, query=query, options=options)
    def iterate(self, *, organization_id: str, query: ListEnabledApplicationsApiV1OrganizationsOrganizationIdApplicationsGetQuery | None = None, identity: Callable[[EnabledApplication], str | int]) -> AsyncIterator[EnabledApplication]:
        return self._operations.list_enabled_applications_api_v1_organizations__organization_id__applications_get_iterate(organization_id=organization_id, query=query, identity=identity)
    async def delete(self, *, organization_id: str, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.disable_application_api_v1_organizations__organization_id__applications__application_id__delete(organization_id=organization_id, application_id=application_id, options=options)
    async def get(self, *, organization_id: str, application_id: str, options: WriteOptions | None = None) -> ApiResult[EnabledApplication]:
        return await self._operations.get_enabled_application_api_v1_organizations__organization_id__applications__application_id__get(organization_id=organization_id, application_id=application_id, options=options)
    async def replace(self, *, organization_id: str, application_id: str, options: WriteOptions | None = None, body: EnableApplication) -> ApiResult[EnabledApplication]:
        return await self._operations.enable_application_api_v1_organizations__organization_id__applications__application_id__put(organization_id=organization_id, application_id=application_id, options=options, body=body)

class ResourceOrganizationsBranding:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def delete(self, *, organization_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.remove_organization_api_v1_organizations__organization_id__branding_delete(organization_id=organization_id, options=options)
    async def get(self, *, organization_id: str, options: WriteOptions | None = None) -> ApiResult[BrandingResource]:
        return await self._operations.read_organization_api_v1_organizations__organization_id__branding_get(organization_id=organization_id, options=options)
    async def update(self, *, organization_id: str, options: WriteOptions | None = None, body: Theme) -> ApiResult[BrandingResource]:
        return await self._operations.patch_organization_api_v1_organizations__organization_id__branding_patch(organization_id=organization_id, options=options, body=body)

class ResourceOrganizationsChannels:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.identity = ResourceOrganizationsChannelsIdentity(operations)
        self.test = ResourceOrganizationsChannelsTest(operations)
        self.verify = ResourceOrganizationsChannelsVerify(operations)
    async def list(self, *, organization_id: str, query: ListOrganizationApiV1OrganizationsOrganizationIdChannelsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ChannelList]:
        return await self._operations.list_organization_api_v1_organizations__organization_id__channels_get(organization_id=organization_id, query=query, options=options)
    def iterate(self, *, organization_id: str, query: ListOrganizationApiV1OrganizationsOrganizationIdChannelsGetQuery | None = None, identity: Callable[[ChannelResource], str | int]) -> AsyncIterator[ChannelResource]:
        return self._operations.list_organization_api_v1_organizations__organization_id__channels_get_iterate(organization_id=organization_id, query=query, identity=identity)
    async def delete(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.remove_organization_api_v1_organizations__organization_id__channels__channel_type__delete(channel_type=channel_type, organization_id=organization_id, options=options)
    async def get(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: WriteOptions | None = None) -> ApiResult[ChannelResource]:
        return await self._operations.read_organization_api_v1_organizations__organization_id__channels__channel_type__get(channel_type=channel_type, organization_id=organization_id, options=options)
    async def update(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], organization_id: str, options: WriteOptions | None = None, body: ChannelPatch) -> ApiResult[ChannelResource]:
        return await self._operations.patch_organization_api_v1_organizations__organization_id__channels__channel_type__patch(channel_type=channel_type, organization_id=organization_id, options=options, body=body)

class ResourceOrganizationsConnections:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, organization_id: str, query: ListOrgConnectionsApiV1OrganizationsOrganizationIdConnectionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ConnectionList]:
        return await self._operations.list_org_connections_api_v1_organizations__organization_id__connections_get(organization_id=organization_id, query=query, options=options)
    def iterate(self, *, organization_id: str, query: ListOrgConnectionsApiV1OrganizationsOrganizationIdConnectionsGetQuery | None = None, identity: Callable[[ConnectionResource], str | int] | None = None) -> AsyncIterator[ConnectionResource]:
        return self._operations.list_org_connections_api_v1_organizations__organization_id__connections_get_iterate(organization_id=organization_id, query=query, identity=identity)
    async def create(self, *, organization_id: str, options: WriteOptions | None = None, body: ConnectionCreate) -> ApiResult[ConnectionResource]:
        return await self._operations.create_org_connection_api_v1_organizations__organization_id__connections_post(organization_id=organization_id, options=options, body=body)
    async def delete(self, *, organization_id: str, connection_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_org_connection_api_v1_organizations__organization_id__connections__connection_id__delete(organization_id=organization_id, connection_id=connection_id, options=options)
    async def get(self, *, organization_id: str, connection_id: str, options: WriteOptions | None = None) -> ApiResult[ConnectionResource]:
        return await self._operations.get_org_connection_api_v1_organizations__organization_id__connections__connection_id__get(organization_id=organization_id, connection_id=connection_id, options=options)
    async def update(self, *, organization_id: str, connection_id: str, options: WriteOptions | None = None, body: ConnectionPatch) -> ApiResult[ConnectionResource]:
        return await self._operations.patch_org_connection_api_v1_organizations__organization_id__connections__connection_id__patch(organization_id=organization_id, connection_id=connection_id, options=options, body=body)

class ResourceOrganizationsConsents:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.impact = ResourceOrganizationsConsentsImpact(operations)
        self.versions = ResourceOrganizationsConsentsVersions(operations)
    async def list(self, *, organization_id: str, query: OrgListApiV1OrganizationsOrganizationIdConsentsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[TermList]:
        return await self._operations.org_list_api_v1_organizations__organization_id__consents_get(organization_id=organization_id, query=query, options=options)
    def iterate(self, *, organization_id: str, query: OrgListApiV1OrganizationsOrganizationIdConsentsGetQuery | None = None, identity: Callable[[TermResource], str | int] | None = None) -> AsyncIterator[TermResource]:
        return self._operations.org_list_api_v1_organizations__organization_id__consents_get_iterate(organization_id=organization_id, query=query, identity=identity)
    async def create(self, *, organization_id: str, options: OrgCreateApiV1OrganizationsOrganizationIdConsentsPostWriteOptions, body: TermCreate) -> ApiResult[TermResource]:
        return await self._operations.org_create_api_v1_organizations__organization_id__consents_post(organization_id=organization_id, options=options, body=body)
    async def delete(self, *, organization_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.org_retire_api_v1_organizations__organization_id__consents__consent_id__delete(organization_id=organization_id, consent_id=consent_id, options=options)
    async def get(self, *, organization_id: str, consent_id: str, options: WriteOptions | None = None) -> ApiResult[TermResource]:
        return await self._operations.org_read_api_v1_organizations__organization_id__consents__consent_id__get(organization_id=organization_id, consent_id=consent_id, options=options)
    async def update(self, *, organization_id: str, consent_id: str, options: WriteOptions | None = None, body: TermPatch) -> ApiResult[TermMutationResponse]:
        return await self._operations.org_patch_api_v1_organizations__organization_id__consents__consent_id__patch(organization_id=organization_id, consent_id=consent_id, options=options, body=body)

class ResourceOrganizationsDomains:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.verify = ResourceOrganizationsDomainsVerify(operations)
    async def list(self, *, organization_id: str, query: ListOrganizationDomainsApiV1OrganizationsOrganizationIdDomainsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[DomainList]:
        return await self._operations.list_organization_domains_api_v1_organizations__organization_id__domains_get(organization_id=organization_id, query=query, options=options)
    def iterate(self, *, organization_id: str, query: ListOrganizationDomainsApiV1OrganizationsOrganizationIdDomainsGetQuery | None = None, identity: Callable[[DomainResource], str | int] | None = None) -> AsyncIterator[DomainResource]:
        return self._operations.list_organization_domains_api_v1_organizations__organization_id__domains_get_iterate(organization_id=organization_id, query=query, identity=identity)
    async def create(self, *, organization_id: str, options: CreateOrganizationDomainApiV1OrganizationsOrganizationIdDomainsPostWriteOptions, body: DomainCreate) -> ApiResult[DomainResource]:
        return await self._operations.create_organization_domain_api_v1_organizations__organization_id__domains_post(organization_id=organization_id, options=options, body=body)
    async def delete(self, *, domain_id: str, organization_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_organization_domain_api_v1_organizations__organization_id__domains__domain_id__delete(domain_id=domain_id, organization_id=organization_id, options=options)
    async def get(self, *, domain_id: str, organization_id: str, options: WriteOptions | None = None) -> ApiResult[DomainResource]:
        return await self._operations.get_organization_domain_api_v1_organizations__organization_id__domains__domain_id__get(domain_id=domain_id, organization_id=organization_id, options=options)
    async def update(self, *, organization_id: str, domain_id: str, options: WriteOptions | None = None, body: AccountDomainPatch | DelegatedDomainPatch) -> ApiResult[DomainResource]:
        return await self._operations.patch_organization_domain_api_v1_organizations__organization_id__domains__domain_id__patch(organization_id=organization_id, domain_id=domain_id, options=options, body=body)

class ResourceOrganizationsMemberships:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, organization_id: str, query: ListMembershipsApiV1OrganizationsOrganizationIdMembershipsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[MembershipList]:
        return await self._operations.list_memberships_api_v1_organizations__organization_id__memberships_get(organization_id=organization_id, query=query, options=options)
    def iterate(self, *, organization_id: str, query: ListMembershipsApiV1OrganizationsOrganizationIdMembershipsGetQuery | None = None, identity: Callable[[MembershipResource], str | int]) -> AsyncIterator[MembershipResource]:
        return self._operations.list_memberships_api_v1_organizations__organization_id__memberships_get_iterate(organization_id=organization_id, query=query, identity=identity)
    async def create(self, *, organization_id: str, options: CreateMembershipApiV1OrganizationsOrganizationIdMembershipsPostWriteOptions, body: MembershipCreate) -> ApiResult[MembershipResource]:
        return await self._operations.create_membership_api_v1_organizations__organization_id__memberships_post(organization_id=organization_id, options=options, body=body)
    async def delete(self, *, organization_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_membership_api_v1_organizations__organization_id__memberships__user_id__delete(organization_id=organization_id, user_id=user_id, options=options)
    async def get(self, *, organization_id: str, user_id: str, options: WriteOptions | None = None) -> ApiResult[MembershipResource]:
        return await self._operations.get_membership_api_v1_organizations__organization_id__memberships__user_id__get(organization_id=organization_id, user_id=user_id, options=options)
    async def update(self, *, organization_id: str, user_id: str, options: WriteOptions | None = None, body: MembershipPatch) -> ApiResult[MembershipResource]:
        return await self._operations.patch_membership_api_v1_organizations__organization_id__memberships__user_id__patch(organization_id=organization_id, user_id=user_id, options=options, body=body)

class ResourceSupportVerification:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, options: VerificationAccountApiV1SupportVerificationPostWriteOptions, body: EmptyRequest) -> ApiResult[VerificationQueued]:
        return await self._operations.verification_account_api_v1_support_verification_post(options=options, body=body)

class ResourceUsersApprove:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, user_id: str, options: ApproveUserApiV1UsersUserIdApprovePostWriteOptions) -> ApiResult[UserResource]:
        return await self._operations.approve_user_api_v1_users__user_id__approve_post(user_id=user_id, options=options)

class ResourceUsersExport:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, user_id: str, options: WriteOptions | None = None) -> ApiResult[Any]:
        return await self._operations.export_user_api_v1_users__user_id__export_get(user_id=user_id, options=options)

class ResourceUsersMemberships:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, user_id: str, query: ListUserMembershipsApiV1UsersUserIdMembershipsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[MembershipList]:
        return await self._operations.list_user_memberships_api_v1_users__user_id__memberships_get(user_id=user_id, query=query, options=options)
    def iterate(self, *, user_id: str, query: ListUserMembershipsApiV1UsersUserIdMembershipsGetQuery | None = None, identity: Callable[[MembershipResource], str | int]) -> AsyncIterator[MembershipResource]:
        return self._operations.list_user_memberships_api_v1_users__user_id__memberships_get_iterate(user_id=user_id, query=query, identity=identity)

class ResourceUsersMfa:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.reset = ResourceUsersMfaReset(operations)

class ResourceUsersProcessingBlock:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def delete(self, *, user_id: str, options: UnblockProcessingApiV1UsersUserIdProcessingBlockDeleteWriteOptions) -> ApiResult[UserResource]:
        return await self._operations.unblock_processing_api_v1_users__user_id__processing_block_delete(user_id=user_id, options=options)
    async def create(self, *, user_id: str, options: BlockProcessingApiV1UsersUserIdProcessingBlockPostWriteOptions) -> ApiResult[UserResource]:
        return await self._operations.block_processing_api_v1_users__user_id__processing_block_post(user_id=user_id, options=options)

class ResourceUsersRecovery:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, user_id: str, options: IssueRecoveryApiV1UsersUserIdRecoveryPostWriteOptions) -> ApiResult[RecoveryResult]:
        return await self._operations.issue_recovery_api_v1_users__user_id__recovery_post(user_id=user_id, options=options)

class ResourceUsersReject:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, user_id: str, options: RejectUserApiV1UsersUserIdRejectPostWriteOptions) -> ApiResult[UserDeletionResult]:
        return await self._operations.reject_user_api_v1_users__user_id__reject_post(user_id=user_id, options=options)

class ResourceUsersSessions:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.revoke = ResourceUsersSessionsRevoke(operations)
    async def list(self, *, user_id: str, query: ListSessionsApiV1UsersUserIdSessionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[SessionList]:
        return await self._operations.list_sessions_api_v1_users__user_id__sessions_get(user_id=user_id, query=query, options=options)
    def iterate(self, *, user_id: str, query: ListSessionsApiV1UsersUserIdSessionsGetQuery | None = None, identity: Callable[[SessionResource], str | int] | None = None) -> AsyncIterator[SessionResource]:
        return self._operations.list_sessions_api_v1_users__user_id__sessions_get_iterate(user_id=user_id, query=query, identity=identity)
    async def delete(self, *, user_id: str, session_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_session_api_v1_users__user_id__sessions__session_id__delete(user_id=user_id, session_id=session_id, options=options)
    async def get(self, *, user_id: str, session_id: str, options: WriteOptions | None = None) -> ApiResult[SessionResource]:
        return await self._operations.get_session_api_v1_users__user_id__sessions__session_id__get(user_id=user_id, session_id=session_id, options=options)

class ResourceWebhookDeliveriesRetry:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, delivery_id: str, options: RetryDeliveryApiV1WebhookDeliveriesDeliveryIdRetryPostWriteOptions, body: Empty) -> ApiResult[DeliveryResource]:
        return await self._operations.retry_delivery_api_v1_webhook_deliveries__delivery_id__retry_post(delivery_id=delivery_id, options=options, body=body)

class ResourceWebhookEndpointsDestinationChanges:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, endpoint_id: str, options: ChangeDestinationApiV1WebhookEndpointsEndpointIdDestinationChangesPostWriteOptions, body: DestinationChange) -> ApiResult[StwrdIdpAdminApiWebhookEndpointsRotationResource]:
        return await self._operations.change_destination_api_v1_webhook_endpoints__endpoint_id__destination_changes_post(endpoint_id=endpoint_id, options=options, body=body)

class ResourceWebhookEndpointsSecret:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.reveal = ResourceWebhookEndpointsSecretReveal(operations)

class ResourceWebhookEndpointsSecretRotations:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, endpoint_id: str, options: RotateEndpointApiV1WebhookEndpointsEndpointIdSecretRotationsPostWriteOptions, body: RotationCreate) -> ApiResult[StwrdIdpAdminApiWebhookEndpointsRotationResource]:
        return await self._operations.rotate_endpoint_api_v1_webhook_endpoints__endpoint_id__secret_rotations_post(endpoint_id=endpoint_id, options=options, body=body)

class ResourceWebhookEndpointsTest:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, endpoint_id: str, options: TestEndpointApiV1WebhookEndpointsEndpointIdTestPostWriteOptions, body: Empty) -> ApiResult[TestResource]:
        return await self._operations.test_endpoint_api_v1_webhook_endpoints__endpoint_id__test_post(endpoint_id=endpoint_id, options=options, body=body)

class ResourceAccountPolicy:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, options: WriteOptions | None = None) -> ApiResult[AccountPolicyResource]:
        return await self._operations.get_account_policy_api_v1_account_policy_get(options=options)
    async def update(self, *, options: WriteOptions | None = None, body: AccountPolicyPatch) -> ApiResult[AccountPolicyResource]:
        return await self._operations.patch_account_policy_api_v1_account_policy_patch(options=options, body=body)

class ResourceApplications:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.agent_instructions = ResourceApplicationsAgentInstructions(operations)
        self.authentication = ResourceApplicationsAuthentication(operations)
        self.branding = ResourceApplicationsBranding(operations)
        self.channels = ResourceApplicationsChannels(operations)
        self.claims = ResourceApplicationsClaims(operations)
        self.consent_receipt = ResourceApplicationsConsentReceipt(operations)
        self.consents = ResourceApplicationsConsents(operations)
        self.domains = ResourceApplicationsDomains(operations)
        self.permissions = ResourceApplicationsPermissions(operations)
        self.roles = ResourceApplicationsRoles(operations)
        self.secret = ResourceApplicationsSecret(operations)
        self.secret_rotations = ResourceApplicationsSecretRotations(operations)
        self.support = ResourceApplicationsSupport(operations)
        self.test_login = ResourceApplicationsTestLogin(operations)
        self.tokens = ResourceApplicationsTokens(operations)
        self.users = ResourceApplicationsUsers(operations)
    async def list(self, *, query: ListApplicationsApiV1ApplicationsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ApplicationList]:
        return await self._operations.list_applications_api_v1_applications_get(query=query, options=options)
    def iterate(self, *, query: ListApplicationsApiV1ApplicationsGetQuery | None = None, identity: Callable[[Application], str | int] | None = None) -> AsyncIterator[Application]:
        return self._operations.list_applications_api_v1_applications_get_iterate(query=query, identity=identity)
    async def create(self, *, options: CreateApplicationApiV1ApplicationsPostWriteOptions, body: ApplicationCreate) -> ApiResult[Application]:
        return await self._operations.create_application_api_v1_applications_post(options=options, body=body)
    async def delete(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_application_api_v1_applications__application_id__delete(application_id=application_id, options=options)
    async def get(self, *, application_id: str, options: WriteOptions | None = None) -> ApiResult[Application]:
        return await self._operations.get_application_api_v1_applications__application_id__get(application_id=application_id, options=options)
    async def update(self, *, application_id: str, options: WriteOptions | None = None, body: ApplicationPatch) -> ApiResult[Application]:
        return await self._operations.patch_application_api_v1_applications__application_id__patch(application_id=application_id, options=options, body=body)

class ResourceAuditEvents:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, query: AuditEventsApiV1AuditEventsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[AuditEventList]:
        return await self._operations.audit_events_api_v1_audit_events_get(query=query, options=options)
    def iterate(self, *, query: AuditEventsApiV1AuditEventsGetQuery | None = None, identity: Callable[[AuditEventResource], str | int] | None = None) -> AsyncIterator[AuditEventResource]:
        return self._operations.audit_events_api_v1_audit_events_get_iterate(query=query, identity=identity)

class ResourceBranding:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.assets = ResourceBrandingAssets(operations)
        self.login_preview = ResourceBrandingLoginPreview(operations)
        self.seal = ResourceBrandingSeal(operations)
    async def delete(self, *, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.remove_account_api_v1_branding_delete(options=options)
    async def get(self, *, options: WriteOptions | None = None) -> ApiResult[BrandingResource]:
        return await self._operations.read_account_api_v1_branding_get(options=options)
    async def update(self, *, options: WriteOptions | None = None, body: Theme) -> ApiResult[BrandingResource]:
        return await self._operations.patch_account_api_v1_branding_patch(options=options, body=body)

class ResourceChannels:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.identity = ResourceChannelsIdentity(operations)
        self.test = ResourceChannelsTest(operations)
        self.verify = ResourceChannelsVerify(operations)
    async def list(self, *, query: ListAccountApiV1ChannelsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ChannelList]:
        return await self._operations.list_account_api_v1_channels_get(query=query, options=options)
    def iterate(self, *, query: ListAccountApiV1ChannelsGetQuery | None = None, identity: Callable[[ChannelResource], str | int]) -> AsyncIterator[ChannelResource]:
        return self._operations.list_account_api_v1_channels_get_iterate(query=query, identity=identity)
    async def delete(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.remove_account_api_v1_channels__channel_type__delete(channel_type=channel_type, options=options)
    async def get(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: WriteOptions | None = None) -> ApiResult[ChannelResource]:
        return await self._operations.read_account_api_v1_channels__channel_type__get(channel_type=channel_type, options=options)
    async def update(self, *, channel_type: Literal['email'] | Literal['sms'] | Literal['whatsapp'], options: WriteOptions | None = None, body: ChannelPatch) -> ApiResult[ChannelResource]:
        return await self._operations.patch_account_api_v1_channels__channel_type__patch(channel_type=channel_type, options=options, body=body)

class ResourceConnections:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, query: ListConnectionsApiV1ConnectionsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ConnectionList]:
        return await self._operations.list_connections_api_v1_connections_get(query=query, options=options)
    def iterate(self, *, query: ListConnectionsApiV1ConnectionsGetQuery | None = None, identity: Callable[[ConnectionResource], str | int] | None = None) -> AsyncIterator[ConnectionResource]:
        return self._operations.list_connections_api_v1_connections_get_iterate(query=query, identity=identity)
    async def create(self, *, options: WriteOptions | None = None, body: ConnectionCreate) -> ApiResult[ConnectionResource]:
        return await self._operations.create_connection_api_v1_connections_post(options=options, body=body)
    async def delete(self, *, connection_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_connection_api_v1_connections__connection_id__delete(connection_id=connection_id, options=options)
    async def get(self, *, connection_id: str, options: WriteOptions | None = None) -> ApiResult[ConnectionResource]:
        return await self._operations.get_connection_api_v1_connections__connection_id__get(connection_id=connection_id, options=options)
    async def update(self, *, connection_id: str, options: WriteOptions | None = None, body: ConnectionPatch) -> ApiResult[ConnectionResource]:
        return await self._operations.patch_connection_api_v1_connections__connection_id__patch(connection_id=connection_id, options=options, body=body)

class ResourceConsentActs:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.revoke = ResourceConsentActsRevoke(operations)
    async def list(self, *, query: GetActsApiV1ConsentActsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[ActList]:
        return await self._operations.get_acts_api_v1_consent_acts_get(query=query, options=options)
    def iterate(self, *, query: GetActsApiV1ConsentActsGetQuery | None = None, identity: Callable[[ActResource], str | int] | None = None) -> AsyncIterator[ActResource]:
        return self._operations.get_acts_api_v1_consent_acts_get_iterate(query=query, identity=identity)
    async def get(self, *, act_id: str, options: WriteOptions | None = None) -> ApiResult[ActResource]:
        return await self._operations.get_act_api_v1_consent_acts__act_id__get(act_id=act_id, options=options)

class ResourceConsentDocuments:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, digest: str, options: WriteOptions | None = None) -> ApiResult[bytes]:
        return await self._operations.get_document_api_v1_consent_documents__digest__get(digest=digest, options=options)

class ResourceConsentRetention:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, options: WriteOptions | None = None) -> ApiResult[RetentionResource]:
        return await self._operations.get_retention_api_v1_consent_retention_get(options=options)
    async def update(self, *, options: WriteOptions | None = None, body: RetentionPatch) -> ApiResult[RetentionResource]:
        return await self._operations.patch_retention_api_v1_consent_retention_patch(options=options, body=body)

class ResourceContext:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, options: WriteOptions | None = None) -> ApiResult[ContextResource]:
        return await self._operations.credential_context_api_v1_context_get(options=options)

class ResourceDomains:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.verify = ResourceDomainsVerify(operations)
    async def list(self, *, query: ListAccountDomainsApiV1DomainsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[DomainList]:
        return await self._operations.list_account_domains_api_v1_domains_get(query=query, options=options)
    def iterate(self, *, query: ListAccountDomainsApiV1DomainsGetQuery | None = None, identity: Callable[[DomainResource], str | int] | None = None) -> AsyncIterator[DomainResource]:
        return self._operations.list_account_domains_api_v1_domains_get_iterate(query=query, identity=identity)
    async def create(self, *, options: CreateAccountDomainApiV1DomainsPostWriteOptions, body: DomainCreate) -> ApiResult[DomainResource]:
        return await self._operations.create_account_domain_api_v1_domains_post(options=options, body=body)
    async def delete(self, *, domain_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_account_domain_api_v1_domains__domain_id__delete(domain_id=domain_id, options=options)
    async def get(self, *, domain_id: str, options: WriteOptions | None = None) -> ApiResult[DomainResource]:
        return await self._operations.get_account_domain_api_v1_domains__domain_id__get(domain_id=domain_id, options=options)

class ResourceInvitations:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.resend = ResourceInvitationsResend(operations)
    async def list(self, *, query: ListInvitationsApiV1InvitationsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[InvitationList]:
        return await self._operations.list_invitations_api_v1_invitations_get(query=query, options=options)
    def iterate(self, *, query: ListInvitationsApiV1InvitationsGetQuery | None = None, identity: Callable[[InvitationResource], str | int] | None = None) -> AsyncIterator[InvitationResource]:
        return self._operations.list_invitations_api_v1_invitations_get_iterate(query=query, identity=identity)
    async def create(self, *, options: CreateInvitationApiV1InvitationsPostWriteOptions, body: InvitationCreate) -> ApiResult[InvitationResource]:
        return await self._operations.create_invitation_api_v1_invitations_post(options=options, body=body)
    async def delete(self, *, invitation_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.cancel_invitation_api_v1_invitations__invitation_id__delete(invitation_id=invitation_id, options=options)
    async def get(self, *, invitation_id: str, options: WriteOptions | None = None) -> ApiResult[InvitationResource]:
        return await self._operations.get_invitation_api_v1_invitations__invitation_id__get(invitation_id=invitation_id, options=options)

class ResourceMe:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.memberships = ResourceMeMemberships(operations)
    async def get(self, *, options: WriteOptions | None = None) -> ApiResult[SelfUserResource]:
        return await self._operations.self_user_api_v1_me_get(options=options)

class ResourceMessages:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, query: ListMessagesApiV1MessagesGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[MessageList]:
        return await self._operations.list_messages_api_v1_messages_get(query=query, options=options)
    def iterate(self, *, query: ListMessagesApiV1MessagesGetQuery | None = None, identity: Callable[[MessageResource], str | int] | None = None) -> AsyncIterator[MessageResource]:
        return self._operations.list_messages_api_v1_messages_get_iterate(query=query, identity=identity)

class ResourceOrganizationAdminPolicy:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def get(self, *, options: WriteOptions | None = None) -> ApiResult[AdministrativePolicy]:
        return await self._operations.get_policy_api_v1_organization_admin_policy_get(options=options)
    async def update(self, *, options: WriteOptions | None = None, body: AdministrativePolicyPatch) -> ApiResult[AdministrativePolicy]:
        return await self._operations.patch_policy_api_v1_organization_admin_policy_patch(options=options, body=body)

class ResourceOrganizations:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.applications = ResourceOrganizationsApplications(operations)
        self.branding = ResourceOrganizationsBranding(operations)
        self.channels = ResourceOrganizationsChannels(operations)
        self.connections = ResourceOrganizationsConnections(operations)
        self.consents = ResourceOrganizationsConsents(operations)
        self.domains = ResourceOrganizationsDomains(operations)
        self.memberships = ResourceOrganizationsMemberships(operations)
    async def list(self, *, query: ListOrganizationsApiV1OrganizationsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[OrganizationList]:
        return await self._operations.list_organizations_api_v1_organizations_get(query=query, options=options)
    def iterate(self, *, query: ListOrganizationsApiV1OrganizationsGetQuery | None = None, identity: Callable[[OrganizationResource], str | int] | None = None) -> AsyncIterator[OrganizationResource]:
        return self._operations.list_organizations_api_v1_organizations_get_iterate(query=query, identity=identity)
    async def create(self, *, options: CreateOrganizationApiV1OrganizationsPostWriteOptions, body: OrganizationCreate) -> ApiResult[OrganizationResource]:
        return await self._operations.create_organization_api_v1_organizations_post(options=options, body=body)
    async def delete(self, *, organization_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_organization_api_v1_organizations__organization_id__delete(organization_id=organization_id, options=options)
    async def get(self, *, organization_id: str, options: WriteOptions | None = None) -> ApiResult[OrganizationResource]:
        return await self._operations.get_organization_api_v1_organizations__organization_id__get(organization_id=organization_id, options=options)
    async def update(self, *, organization_id: str, options: WriteOptions | None = None, body: OrganizationPatch) -> ApiResult[OrganizationResource]:
        return await self._operations.patch_organization_api_v1_organizations__organization_id__patch(organization_id=organization_id, options=options, body=body)

class ResourceSigningKeys:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, query: GetKeysApiV1SigningKeysGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[SigningKeyList]:
        return await self._operations.get_keys_api_v1_signing_keys_get(query=query, options=options)
    def iterate(self, *, query: GetKeysApiV1SigningKeysGetQuery | None = None, identity: Callable[[SigningKeyResource], str | int] | None = None) -> AsyncIterator[SigningKeyResource]:
        return self._operations.get_keys_api_v1_signing_keys_get_iterate(query=query, identity=identity)

class ResourceStepUp:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def create(self, *, options: WriteOptions | None = None, body: StepUpRequest) -> ApiResult[dict[str, Any]]:
        return await self._operations.request_step_up_api_v1_step_up_post(options=options, body=body)

class ResourceSupport:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.verification = ResourceSupportVerification(operations)
    async def delete(self, *, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.remove_account_api_v1_support_delete(options=options)
    async def get(self, *, options: WriteOptions | None = None) -> ApiResult[SupportResource]:
        return await self._operations.read_account_api_v1_support_get(options=options)
    async def update(self, *, options: WriteOptions | None = None, body: SupportPatch) -> ApiResult[SupportResource]:
        return await self._operations.patch_account_api_v1_support_patch(options=options, body=body)

class ResourceUsers:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.approve = ResourceUsersApprove(operations)
        self.export = ResourceUsersExport(operations)
        self.memberships = ResourceUsersMemberships(operations)
        self.mfa = ResourceUsersMfa(operations)
        self.processing_block = ResourceUsersProcessingBlock(operations)
        self.recovery = ResourceUsersRecovery(operations)
        self.reject = ResourceUsersReject(operations)
        self.sessions = ResourceUsersSessions(operations)
    async def list(self, *, query: ListUsersApiV1UsersGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[UserList]:
        return await self._operations.list_users_api_v1_users_get(query=query, options=options)
    def iterate(self, *, query: ListUsersApiV1UsersGetQuery | None = None, identity: Callable[[UserResource], str | int] | None = None) -> AsyncIterator[UserResource]:
        return self._operations.list_users_api_v1_users_get_iterate(query=query, identity=identity)
    async def create(self, *, options: CreateUserApiV1UsersPostWriteOptions, body: UserCreate) -> ApiResult[UserResource]:
        return await self._operations.create_user_api_v1_users_post(options=options, body=body)
    async def delete(self, *, user_id: str, options: DeleteUserApiV1UsersUserIdDeleteWriteOptions) -> ApiResult[UserDeletionResult]:
        return await self._operations.delete_user_api_v1_users__user_id__delete(user_id=user_id, options=options)
    async def get(self, *, user_id: str, options: WriteOptions | None = None) -> ApiResult[UserResource]:
        return await self._operations.get_user_api_v1_users__user_id__get(user_id=user_id, options=options)
    async def update(self, *, user_id: str, options: WriteOptions | None = None, body: UserPatch) -> ApiResult[UserResource]:
        return await self._operations.patch_user_api_v1_users__user_id__patch(user_id=user_id, options=options, body=body)

class ResourceWebhookDeliveries:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.retry = ResourceWebhookDeliveriesRetry(operations)
    async def list(self, *, query: ListDeliveriesApiV1WebhookDeliveriesGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[DeliveryList]:
        return await self._operations.list_deliveries_api_v1_webhook_deliveries_get(query=query, options=options)
    def iterate(self, *, query: ListDeliveriesApiV1WebhookDeliveriesGetQuery | None = None, identity: Callable[[DeliveryResource], str | int] | None = None) -> AsyncIterator[DeliveryResource]:
        return self._operations.list_deliveries_api_v1_webhook_deliveries_get_iterate(query=query, identity=identity)
    async def get(self, *, delivery_id: str, options: WriteOptions | None = None) -> ApiResult[DeliveryResource]:
        return await self._operations.get_delivery_api_v1_webhook_deliveries__delivery_id__get(delivery_id=delivery_id, options=options)

class ResourceWebhookEndpoints:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
        self.destination_changes = ResourceWebhookEndpointsDestinationChanges(operations)
        self.secret = ResourceWebhookEndpointsSecret(operations)
        self.secret_rotations = ResourceWebhookEndpointsSecretRotations(operations)
        self.test = ResourceWebhookEndpointsTest(operations)
    async def list(self, *, query: ListEndpointsApiV1WebhookEndpointsGetQuery | None = None, options: WriteOptions | None = None) -> ApiResult[EndpointList]:
        return await self._operations.list_endpoints_api_v1_webhook_endpoints_get(query=query, options=options)
    def iterate(self, *, query: ListEndpointsApiV1WebhookEndpointsGetQuery | None = None, identity: Callable[[EndpointResource], str | int] | None = None) -> AsyncIterator[EndpointResource]:
        return self._operations.list_endpoints_api_v1_webhook_endpoints_get_iterate(query=query, identity=identity)
    async def create(self, *, options: CreateEndpointApiV1WebhookEndpointsPostWriteOptions, body: EndpointCreate) -> ApiResult[EndpointResource]:
        return await self._operations.create_endpoint_api_v1_webhook_endpoints_post(options=options, body=body)
    async def delete(self, *, endpoint_id: str, options: WriteOptions | None = None) -> ApiResult[None]:
        return await self._operations.delete_endpoint_api_v1_webhook_endpoints__endpoint_id__delete(endpoint_id=endpoint_id, options=options)
    async def get(self, *, endpoint_id: str, options: WriteOptions | None = None) -> ApiResult[EndpointResource]:
        return await self._operations.get_endpoint_api_v1_webhook_endpoints__endpoint_id__get(endpoint_id=endpoint_id, options=options)
    async def update(self, *, endpoint_id: str, options: WriteOptions | None = None, body: EndpointPatch) -> ApiResult[EndpointResource]:
        return await self._operations.patch_endpoint_api_v1_webhook_endpoints__endpoint_id__patch(endpoint_id=endpoint_id, options=options, body=body)

class ResourceWebhookEventTypes:
    def __init__(self, operations: ManagementOperations) -> None:
        self._operations = operations
    async def list(self, *, query: EventTypesApiV1WebhookEventTypesGetQuery, options: WriteOptions | None = None) -> ApiResult[EventTypeList]:
        return await self._operations.event_types_api_v1_webhook_event_types_get(query=query, options=options)
    def iterate(self, *, query: EventTypesApiV1WebhookEventTypesGetQuery, identity: Callable[[EventTypeResource], str | int]) -> AsyncIterator[EventTypeResource]:
        return self._operations.event_types_api_v1_webhook_event_types_get_iterate(query=query, identity=identity)

class ManagementClient(ManagementTransport):
    def __init__(self, options: ManagementOptions, *, http_client: httpx.AsyncClient | None = None) -> None:
        super().__init__(options, http_client=http_client)
        self.operations = ManagementOperations(self)
        self.account_policy = ResourceAccountPolicy(self.operations)
        self.applications = ResourceApplications(self.operations)
        self.audit_events = ResourceAuditEvents(self.operations)
        self.branding = ResourceBranding(self.operations)
        self.channels = ResourceChannels(self.operations)
        self.connections = ResourceConnections(self.operations)
        self.consent_acts = ResourceConsentActs(self.operations)
        self.consent_documents = ResourceConsentDocuments(self.operations)
        self.consent_retention = ResourceConsentRetention(self.operations)
        self.context = ResourceContext(self.operations)
        self.domains = ResourceDomains(self.operations)
        self.invitations = ResourceInvitations(self.operations)
        self.me = ResourceMe(self.operations)
        self.messages = ResourceMessages(self.operations)
        self.organization_admin_policy = ResourceOrganizationAdminPolicy(self.operations)
        self.organizations = ResourceOrganizations(self.operations)
        self.signing_keys = ResourceSigningKeys(self.operations)
        self.step_up = ResourceStepUp(self.operations)
        self.support = ResourceSupport(self.operations)
        self.users = ResourceUsers(self.operations)
        self.webhook_deliveries = ResourceWebhookDeliveries(self.operations)
        self.webhook_endpoints = ResourceWebhookEndpoints(self.operations)
        self.webhook_event_types = ResourceWebhookEventTypes(self.operations)

def create_management(options: ManagementOptions, *, http_client: httpx.AsyncClient | None = None) -> ManagementClient:
    return ManagementClient(options, http_client=http_client)


"""API controller for device provisioning."""

from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.domain.value_objects.provision_request import (
    DetectDeviceRequest,
    ProvisionDeviceRequest,
)
from core.use_cases.manage_provisioning_profiles import (
    ManageProvisioningProfilesUseCase,
)
from core.use_cases.provision_device import ProvisionDeviceUseCase
from litestar import Controller, Router, delete, get, post, put

from api.presentation.dto.requests import (
    CreateProvisioningProfileRequest,
    DetectDeviceAPIRequest,
    ProvisionDeviceAPIRequest,
    UpdateProvisioningProfileRequest,
    VerifyProvisionRequest,
)
from api.presentation.dto.responses import (
    APDeviceInfoResponse,
    ProvisioningProfileResponse,
    ProvisionResultResponse,
    ProvisionStepResponse,
    VerifyResultResponse,
)


class ProvisioningProfilesController(Controller):
    path = "/profiles"
    tags = ["Provisioning"]

    @get()
    async def list_profiles(
        self,
        manage_profiles_use_case: ManageProvisioningProfilesUseCase,
    ) -> list[ProvisioningProfileResponse]:
        """List all provisioning profiles."""
        profiles = await manage_profiles_use_case.list_profiles()
        return [_profile_to_response(p) for p in profiles]

    @post()
    async def create_profile(
        self,
        data: CreateProvisioningProfileRequest,
        manage_profiles_use_case: ManageProvisioningProfilesUseCase,
    ) -> ProvisioningProfileResponse:
        """Create a new provisioning profile."""
        profile = ProvisioningProfile(
            name=data.name,
            wifi_ssid=data.wifi_ssid,
            wifi_password=data.wifi_password,
            mqtt_enabled=data.mqtt_enabled,
            mqtt_server=data.mqtt_server,
            mqtt_user=data.mqtt_user,
            mqtt_password=data.mqtt_password,
            mqtt_topic_prefix_template=data.mqtt_topic_prefix_template,
            auth_password=data.auth_password,
            device_name_template=data.device_name_template,
            timezone=data.timezone,
            cloud_enabled=data.cloud_enabled,
            is_default=data.is_default,
        )
        created = await manage_profiles_use_case.create_profile(profile)
        return _profile_to_response(created)

    @get("/{profile_id:int}")
    async def get_profile(
        self,
        profile_id: int,
        manage_profiles_use_case: ManageProvisioningProfilesUseCase,
    ) -> ProvisioningProfileResponse:
        """Get a provisioning profile by ID."""
        profile = await manage_profiles_use_case.get_profile(profile_id)
        return _profile_to_response(profile)

    @put("/{profile_id:int}")
    async def update_profile(
        self,
        profile_id: int,
        data: UpdateProvisioningProfileRequest,
        manage_profiles_use_case: ManageProvisioningProfilesUseCase,
    ) -> ProvisioningProfileResponse:
        """Update a provisioning profile."""
        result = await manage_profiles_use_case.apply_profile_update(
            profile_id,
            name=data.name,
            wifi_ssid=data.wifi_ssid,
            wifi_password=data.wifi_password,
            mqtt_enabled=data.mqtt_enabled,
            mqtt_server=data.mqtt_server,
            mqtt_user=data.mqtt_user,
            mqtt_password=data.mqtt_password,
            mqtt_topic_prefix_template=data.mqtt_topic_prefix_template,
            auth_password=data.auth_password,
            device_name_template=data.device_name_template,
            timezone=data.timezone,
            cloud_enabled=data.cloud_enabled,
            is_default=data.is_default,
        )
        return _profile_to_response(result)

    @delete("/{profile_id:int}")
    async def delete_profile(
        self,
        profile_id: int,
        manage_profiles_use_case: ManageProvisioningProfilesUseCase,
    ) -> None:
        """Delete a provisioning profile."""
        await manage_profiles_use_case.delete_profile(profile_id)

    @post("/{profile_id:int}/set-default")
    async def set_default_profile(
        self,
        profile_id: int,
        manage_profiles_use_case: ManageProvisioningProfilesUseCase,
    ) -> ProvisioningProfileResponse:
        """Set a profile as the default."""
        await manage_profiles_use_case.set_default_profile(profile_id)
        profile = await manage_profiles_use_case.get_profile(profile_id)
        return _profile_to_response(profile)


class ProvisioningController(Controller):
    path = ""
    tags = ["Provisioning"]

    @post("/detect")
    async def detect_device(
        self,
        data: DetectDeviceAPIRequest,
        provision_device_use_case: ProvisionDeviceUseCase,
    ) -> APDeviceInfoResponse:
        """Detect a Shelly device at the given AP IP."""
        request = DetectDeviceRequest(
            device_ip=data.device_ip,
            timeout=data.timeout,
        )
        info = await provision_device_use_case.detect(request)
        return APDeviceInfoResponse(
            device_id=info.device_id,
            mac=info.mac,
            model=info.model,
            generation=info.generation,
            firmware_version=info.firmware_version,
            auth_enabled=info.auth_enabled,
            auth_domain=info.auth_domain,
            app=info.app,
        )

    @post("/provision")
    async def provision_device(
        self,
        data: ProvisionDeviceAPIRequest,
        provision_device_use_case: ProvisionDeviceUseCase,
    ) -> ProvisionResultResponse:
        """Provision a new Shelly device via its AP."""
        request = ProvisionDeviceRequest(
            device_ip=data.device_ip,
            profile_id=data.profile_id,
            timeout=data.timeout,
        )
        result = await provision_device_use_case.execute(request)
        return ProvisionResultResponse(
            success=result.success,
            device_id=result.device_id,
            device_model=result.device_model,
            device_mac=result.device_mac,
            generation=result.generation,
            steps_completed=[
                ProvisionStepResponse(
                    name=s.name,
                    success=s.success,
                    message=s.message,
                    restart_required=s.restart_required,
                )
                for s in result.steps_completed
            ],
            steps_failed=[
                ProvisionStepResponse(
                    name=s.name,
                    success=s.success,
                    message=s.message,
                    restart_required=s.restart_required,
                )
                for s in result.steps_failed
            ],
            final_ip=result.final_ip,
            error=result.error,
            needs_verification=result.needs_verification,
        )

    @post("/verify")
    async def verify_provision(
        self,
        data: VerifyProvisionRequest,
        provision_device_use_case: ProvisionDeviceUseCase,
    ) -> VerifyResultResponse:
        """Verify a provisioned device is reachable on the target network."""
        found_ip = await provision_device_use_case.verify(
            device_mac=data.device_mac,
            scan_targets=data.scan_targets,
            timeout=data.timeout,
        )
        return VerifyResultResponse(
            found=found_ip is not None,
            device_ip=found_ip,
            device_mac=data.device_mac,
        )


provisioning_router = Router(
    path="/provisioning",
    route_handlers=[ProvisioningProfilesController, ProvisioningController],
)


def _profile_to_response(profile: ProvisioningProfile) -> ProvisioningProfileResponse:
    return ProvisioningProfileResponse(
        id=profile.id or 0,
        name=profile.name,
        wifi_ssid=profile.wifi_ssid,
        mqtt_enabled=profile.mqtt_enabled,
        mqtt_server=profile.mqtt_server,
        mqtt_user=profile.mqtt_user,
        mqtt_topic_prefix_template=profile.mqtt_topic_prefix_template,
        device_name_template=profile.device_name_template,
        timezone=profile.timezone,
        cloud_enabled=profile.cloud_enabled,
        is_default=profile.is_default,
        has_wifi_password=profile.wifi_password is not None,
        has_mqtt_password=profile.mqtt_password is not None,
        has_auth_password=profile.auth_password is not None,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )

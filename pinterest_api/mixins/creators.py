from typing import Dict, Any
from ..exceptions import LoginFailedError

class CreatorsMixin:
    """Mixin for Pinterest creator-related functionality."""

    def get_creator_data(self, creator_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a Pinterest creator.
        
        Args:
            creator_id (str): The ID of the creator to get data for
            
        Returns:
            Dict[str, Any]: Creator data including profile information
            
        Raises:
            LoginFailedError: If not logged in or access token is missing
            requests.exceptions.RequestException: For network/API errors
        """
        if not hasattr(self, 'get_access_token'):
            raise LoginFailedError("Login mixin not properly initialized")

        # Fields to retrieve in response
        fields = (
            "partner.{enable_profile_message,contact_phone,contact_phone_country,"
            "biz_ownership_email,id,contact_email,profile_place()},"
            "user.{country,is_country_eligible_for_lead_form_autofill,about,"
            "is_inspirational_merchant,is_gender_eligible_for_lead_form_autofill,"
            "type,age_in_years,implicitly_followed_by_me,profile_reach,creator_level,"
            "is_default_image,is_under_16,is_under_18,video_views,pin_count,"
            "has_archived_boards,is_partner,verified_identity,is_parental_control_passcode_enabled,"
            "id,ip_stela_rec_disabled,explicitly_following_me,ads_only_profile_site,"
            "secret_board_count,invisible_board_count,show_creator_profile,"
            "is_primary_website_verified,is_age_eligible_for_lead_form_autofill,"
            "blocked_by_me,impressum_url,parental_control_anonymized_email,custom_gender,"
            "has_pin_clusters,partner(),profile_cover(),has_created_all_clusters,"
            "full_name,following_count,has_showcase,image_large_url,pronouns,board_count,"
            "vto_beauty_access_status,is_candidate_for_parental_control_passcode,"
            "has_quicksave_board,is_name_eligible_for_lead_form_autofill,gender,"
            "ppa_merchant_id,has_confirmed_email,story_pin_count,follower_count,"
            "image_xlarge_url,most_recent_board_sort_order,weight_loss_ads_opted_out,"
            "explicitly_followed_by_me,quick_saves_pin_count,profile_views,"
            "scheduled_pin_count,pins_done_count,save_behavior,is_ads_only_profile,"
            "collage_draft_count,is_verified_merchant,first_name,has_catalog,"
            "show_discovered_feed,email,should_default_comments_off,last_pin_save_time,"
            "archived_board_count,video_pin_count,eligible_profile_tabs,last_name,"
            "interest_following_count,explicit_board_following_count,avatar_color_index,"
            "is_private_profile,instagram_data,profile_discovered_public,"
            "is_email_eligible_for_lead_form_autofill,website_url,explicit_user_following_count,"
            "login_state,allow_idea_pin_downloads,canonical_merchant_domain,location,"
            "image_medium_url,shopping_rec_disabled,username,should_show_messaging},"
            "profilecoversource.{video(),source_id,source,images[1200x]},"
            "video.{duration,signature,id,video_list[V_HLSV3_MOBILE, V_DASH_HEVC]}"
        )

        return self._handle_request(
            method="GET",
            endpoint=f"/users/{creator_id}/",
            params={'fields': fields}
        )

    def follow_creator(self, creator_id: str) -> Dict[str, Any]:
        """
        Follow a Pinterest creator.
        
        Args:
            creator_id (str): The ID of the creator to follow
            
        Returns:
            Dict[str, Any]: Response data including follow status
            
        Raises:
            LoginFailedError: If not logged in or access token is missing
            requests.exceptions.RequestException: For network/API errors
        """
        if not hasattr(self, 'get_access_token'):
            raise LoginFailedError("Login mixin not properly initialized")

        # Fields to retrieve in response
        fields = (
            "user.{country,gender,type,age_in_years,follower_count,"
            "implicitly_followed_by_me,explicitly_followed_by_me,is_default_image,"
            "is_under_16,is_under_18,save_behavior,is_partner,id,first_name,"
            "should_default_comments_off,show_creator_profile,last_name,"
            "avatar_color_index,is_private_profile,recent_story_pin_images,"
            "custom_gender,partner(),full_name,username,should_show_messaging,"
            "vto_beauty_access_status}"
        )

        data = {
            'invite_code': '',
            'view_type': '4',
            'view_parameter': '3107'
        }

        return self._handle_request(
            method="PUT",
            endpoint=f"/users/{creator_id}/follow/",
            params={'fields': fields},
            data=data
        ) 
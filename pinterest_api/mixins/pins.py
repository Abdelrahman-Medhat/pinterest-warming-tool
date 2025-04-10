from typing import Dict, Any, List
import requests
import time
import random
from ..exceptions import LoginFailedError

class PinsMixin:
    """Mixin for Pinterest pin-related functionality."""

    DEFAULT_BOARD_NAMES = {
        'GENERAL': 'My Saved Pins',
        'PRODUCTS': 'My Shopping List',
        'RECIPES': 'My Recipes',
        'DIY': 'My DIY Projects'
    }

    def react_to_pin(self, pin_id: str, reaction_type: int = 1) -> Dict[str, Any]:
        """
        React to a pin with a specified reaction type.
        
        Args:
            pin_id (str): The ID of the pin to react to
            reaction_type (int): Type of reaction (default is 1 for 'like')
            
        Returns:
            Dict[str, Any]: Response data including reaction counts and status
            
        Raises:
            LoginFailedError: If not logged in or access token is missing
            requests.exceptions.RequestException: For network/API errors
        """
        if not hasattr(self, 'get_access_token'):
            raise LoginFailedError("Login mixin not properly initialized")
            
        # Fields to retrieve in response
        fields = "pin.{total_reaction_count,reaction_by_me,reaction_counts,id}"
        
        params = {
            'reaction_type': reaction_type,
            'fields': fields
        }
        
        return self._handle_request(
            method="POST",
            endpoint=f"/pins/{pin_id}/react/",
            params=params
        )

    def get_boards(self) -> List[Dict[str, Any]]:
        """
        Get user's boards to save pins to.
        
        Returns:
            List[Dict[str, Any]]: List of user's boards
            
        Raises:
            LoginFailedError: If not logged in or access token is missing
            requests.exceptions.RequestException: For network/API errors
        """
        if not hasattr(self, 'get_access_token'):
            raise LoginFailedError("Login mixin not properly initialized")
            
        fields = [
            "board.id",
            "board.name",
            "board.privacy",
            "board.image_cover_url",
            "board.pin_count",
            "board.owner()",
            "board.created_at"
        ]
        
        params = {
            'fields': ','.join(fields),
            'privacy_filter': 'all'
        }
        
        response = self._handle_request(
            method="GET",
            endpoint="/users/me/boards/",
            params=params
        )
        
        return response.get('data', []) if isinstance(response, dict) else []

    def _determine_board_name(self, pin_details: Dict[str, Any]) -> str:
        """Determine appropriate board name based on pin content."""
        # Check if pin has product metadata
        if pin_details.get('rich_metadata', {}).get('product_metadata'):
            return self.DEFAULT_BOARD_NAMES['PRODUCTS']
        
        # Check if pin has recipe metadata
        if pin_details.get('rich_metadata', {}).get('recipe_metadata'):
            return self.DEFAULT_BOARD_NAMES['RECIPES']
        
        # Check pin category
        category = pin_details.get('category', '').lower()
        if 'diy' in category or 'craft' in category:
            return self.DEFAULT_BOARD_NAMES['DIY']
        
        # Check description for keywords
        description = pin_details.get('description', '').lower()
        if 'recipe' in description or 'food' in description:
            return self.DEFAULT_BOARD_NAMES['RECIPES']
        if 'diy' in description or 'craft' in description:
            return self.DEFAULT_BOARD_NAMES['DIY']
        
        # Default to general board
        return self.DEFAULT_BOARD_NAMES['GENERAL']

    def create_board(self, name: str, description: str = None, privacy: str = 'PUBLIC') -> Dict[str, Any]:
        """Create a new board."""
        data = {
            'name': name,
            'description': description or f'Automatically created board for {name.lower()}',
            'privacy': privacy
        }
        
        try:
            return self._handle_request(
                method="POST",
                endpoint="/boards/",
                data=data
            )
        except requests.exceptions.RequestException as e:
            # If board with name exists, try with a unique suffix
            if getattr(e.response, 'status_code', None) == 409:
                import uuid
                unique_name = f"{name} {str(uuid.uuid4())[:4]}"
                return self.create_board(unique_name, description, privacy)
            raise

    def save_pin(self, pin_id: str) -> Dict[str, Any]:
        """
        Save (repin) a pin using the repin endpoint.
        
        Args:
            pin_id (str): ID of the pin to save
            
        Returns:
            Dict[str, Any]: Response data including save status
        """
        if not hasattr(self, 'get_access_token'):
            raise LoginFailedError("Login mixin not properly initialized")

        # Prepare the exact fields parameter as used in the Pinterest API
        fields = (
            "storypinvideoblock.{block_type,video_signature,block_style,video[V_HLSV3_MOBILE, V_DASH_HEVC, "
            "V_HEVC_MP4_T1_V2, V_HEVC_MP4_T2_V2, V_HEVC_MP4_T3_V2, V_HEVC_MP4_T4_V2, V_HEVC_MP4_T5_V2],type},"
            "storypinimageblock.{image_signature,block_type,block_style,type},"
            "linkblock.{image_signature,src_url,normalized_url,block_type,image[345x],text,type,canonical_url},"
            "domain.{official_user()},"
            "collectionpinitem.{image_signature,images,dominant_color,item_id,link,is_editable,pin_id,title,price_value,price_currency},"
            "collectionpin.{collections_header_text,dpa_layout_type,catalog_collection_type,slideshow_collections_aspect_ratio,"
            "is_dynamic_collections,root_pin_id,item_data},"
            "userwebsite.{official_user()},"
            "storypindata.{has_affiliate_products,static_page_count,pages_preview,metadata(),page_count,has_product_pins,total_video_duration},"
            "storypinpage.{layout,image_signature,video_signature,blocks,image_signature_adjusted,"
            "video[V_HLSV3_MOBILE, V_DASH_HEVC, V_HEVC_MP4_T1_V2, V_HEVC_MP4_T2_V2, V_HEVC_MP4_T3_V2, V_HEVC_MP4_T4_V2, V_HEVC_MP4_T5_V2],"
            "style,id,type,music_attributions,should_mute},"
            "pincarouseldata.{index,id,rich_summary(),rich_metadata(),carousel_slots},"
            "pincarouselslot.{rich_summary,item_id,domain,android_deep_link,link,details,images[345x,750x],id,ad_destination_url,title,rich_metadata},"
            "pin.{comment_count,is_eligible_for_related_products,shopping_flags,pinner(),promoted_is_lead_ad,ad_match_reason,"
            "destination_url_type,promoted_quiz_pin_data,promoted_is_showcase,type,carousel_data(),image_crop,story_pin_data_id,"
            "call_to_create_responses_count,promoted_is_removable,is_owned_by_viewer,digital_media_source_type,auto_alt_text,id,"
            "ad_destination_url,embed,ad_group_id,rich_summary(),grid_title,native_creator(),insertion_id,cacheable_id,source_interest(),"
            "is_native,has_variants,campaign_id_reformatted,promoted_is_auto_assembled,is_premiere,is_eligible_for_web_closeup,"
            "promoted_is_quiz,done_by_me,closeup_description,creative_enhancement_slideshow_aspect_ratio,promoted_android_deep_link,"
            "is_oos_product,attribution_source_id,is_video,promoted_is_catalog_carousel_ad,dominant_color,virtual_try_on_type,"
            "promoted_is_sideswipe_disabled,domain,call_to_action_text,is_stale_product,link_domain(),music_attributions,"
            "collection_pin(),shopping_mdl_browser_type,is_promoted,ad_data(),recommendation_reason,ad_targeting_attribution(),link,"
            "sponsorship,is_unsafe,is_hidden,description,created_at,link_user_website(),title,advertiser_id,is_cpc_ad,is_scene,"
            "image_signature,promoted_is_max_video,is_eligible_for_pre_loved_goods_label,tracking_params,alt_text,dpa_creative_type,"
            "promoted_lead_form(),is_eligible_for_pdp,is_visualization_enabled,is_unsafe_for_comments,is_call_to_create,"
            "ip_eligible_for_stela,dark_profile_link,via_pinner,is_downstream_promotion,promoter(),should_open_in_stream,shuffle(),"
            "aggregated_pin_data(),is_repin,videos(),is_product_tagging_enabled_standard_pin,top_interest,category,story_pin_data(),"
            "should_mute,board(),is_virtual_try_on},"
            "user.{country,gender,type,age_in_years,follower_count,explicitly_followed_by_me,is_default_image,is_under_16,is_under_18,"
            "save_behavior,is_partner,id,is_verified_merchant,first_name,should_default_comments_off,show_creator_profile,last_name,"
            "avatar_color_index,is_private_profile,custom_gender,partner(),full_name,allow_idea_pin_downloads,image_medium_url,username,"
            "should_show_messaging,vto_beauty_access_status},"
            "board.{has_custom_cover,is_collaborative,collaborating_users(),created_at,privacy,should_show_shop_feed,type,is_ads_only,"
            "url,image_cover_url,layout,collaborated_by_me,followed_by_me,should_show_board_collaborators,tracking_params,owner(),name,"
            "collaborator_invites_enabled,action,section_count,id,category},"
            "video.{duration,id,video_list[V_HLSV3_MOBILE, V_DASH_HEVC]},"
            "richpinproductmetadata.{label_info,offers,additional_images,has_multi_images,shipping_info,offer_summary,item_set_id,"
            "item_id,name,id,type,brand},"
            "aggregatedpindata.{is_shop_the_look,comment_count,collections_header_text,is_stela,dpa_layout_type,has_xy_tags,pin_tags,"
            "did_it_data,catalog_collection_type,slideshow_collections_aspect_ratio,aggregated_stats,id,is_dynamic_collections,pin_tags_chips},"
            "shuffle.{tracking_params,source_app_type_detailed,id},"
            "pin.images[200x,236x,736x,474x],"
            "storypinimageblock.image[200x,236x,736x,474x],"
            "storypinpage.image[200x,236x,736x,1200x,474x],"
            "storypinpage.image_adjusted[200x,236x,736x,1200x,474x]"
        )

        # Prepare the data for the repin request with exact parameters
        data = {
            'fields': fields,
            'description': '',
            'share_facebook': '0',
            'share_twitter': '0',
            'disable_comments': '0',
            'disable_did_it': '0',
            'carousel_slot_index': '0'
        }

        # Make the repin request with automatic retry handling
        response = self._handle_request(
            method="POST",
            endpoint=f"/pins/{pin_id}/repin/",
            data=data
        )

        # Add a small delay to prevent rate limiting
        time.sleep(random.uniform(0.5, 1.5))

        return response

    def simulate_pin_open(self, pin_id: str) -> Dict[str, Any]:
        """
        Simulate opening a pin by making necessary API calls and adding realistic delays.
        
        Args:
            pin_id (str): ID of the pin to simulate opening
            
        Returns:
            Dict[str, Any]: Timing and status information
            
        Raises:
            LoginFailedError: If not logged in or access token is missing
            requests.exceptions.RequestException: For network/API errors
        """
        result = {
            'success': False,
            'timing': {
                'load_time': 0,
                'view_time': 0,
                'total_time': 0
            }
        }
        
        start_time = time.time()
        
        try:
            # Simulate initial loading time
            loading_delay = random.uniform(0.5, 1.5)
            time.sleep(loading_delay)
            result['timing']['load_time'] = loading_delay
            
            # Get pin data (this actually makes the API call)
            pin_data = self.get_pin_data(pin_id)
            
            # Simulate viewing time
            view_time = random.uniform(2, 4)
            time.sleep(view_time)
            result['timing']['view_time'] = view_time
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
        finally:
            result['timing']['total_time'] = time.time() - start_time
            
        return result

    def get_pin_data(
        self,
        pin_id: str,
        view_type: int = 1,
        view_parameter: int = 92
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific pin.

        Args:
            pin_id (str): The ID of the pin to retrieve
            view_type (int, optional): View type parameter. Defaults to 1.
            view_parameter (int, optional): View parameter. Defaults to 92.

        Returns:
            Dict[str, Any]: Detailed pin information including media, comments, reactions, etc.

        Raises:
            requests.exceptions.RequestException: For network/API errors
        """
        # Define the fields to retrieve
        fields = [
            "domain.{name,id,official_user()}",
            "collectionpinitem.{image_signature,images,dominant_color,item_id,link,is_editable,pin_id,title,price_value,price_currency}",
            "collectionpin.{collections_header_text,catalog_collection_type,slideshow_collections_aspect_ratio,is_dynamic_collections,root_pin_id,item_data}",
            "userwebsite.{id,official_user()}",
            "storypindata.{has_affiliate_products,metadata(),page_count,has_product_pins}",
            "pincarouseldata.{index,id,rich_summary(),rich_metadata(),carousel_slots}",
            "pincarouselslot.{rich_summary,item_id,domain,android_deep_link,link,details,images[345x,750x],id,ad_destination_url,title,rich_metadata}",
            "shuffleitemimage.{id,user}",
            "pinnote.{updated_at,created_at,id,text,type}",
            "diditdata.{rating,recommend_scores}",
            "pin.{comment_count,is_eligible_for_related_products,native_pin_stats,promoted_quiz_pin_data,type,promoted_is_removable,"
            "auto_alt_text,edited_fields,id,embed,ad_destination_url,rich_summary(),grid_title,native_creator(),is_native,"
            "has_displayable_community_content,unified_user_note,has_variants,is_premiere,section(),promoted_is_quiz,done_by_me,"
            "promoted_android_deep_link,is_instagram_api,is_oos_product,reaction_by_me,dominant_color,formatted_description,"
            "virtual_try_on_type,pin_note(),domain,did_it_disabled,is_stale_product,media_attribution(),is_v1_idea_pin,"
            "favorite_user_count,collection_pin(),shopping_mdl_browser_type,ad_data(),created_at,tracked_link,is_go_linkless,"
            "highlighted_aggregated_comments,is_scene,total_reaction_count,is_eligible_for_aggregated_comments,tracking_params,"
            "shuffle_asset(),digital_media_source_type_label,is_eligible_for_pdp,closeup_unified_description,is_unsafe_for_comments,"
            "is_call_to_create,promoter(),reaction_counts,should_open_in_stream,is_repin,aggregated_pin_data(),should_mute,"
            "story_pin_data(),board(),is_whitelisted_for_tried_it,closeup_attribution,shopping_flags,pinner(),promoted_is_showcase,"
            "carousel_data(),story_pin_data_id,favorited_by_me,comments_disabled,ad_group_id,cacheable_id,origin_pinner(),"
            "user_mention_tags,promoted_is_auto_assembled,rich_metadata(),closeup_description,is_video,promoted_is_catalog_carousel_ad,"
            "can_delete_did_it_and_comments,promoted_is_sideswipe_disabled,call_to_action_text,link_domain(),canonical_merchant_name,"
            "music_attributions,is_promoted,board_conversation_thread,hashtags,ad_targeting_attribution(),link,sponsorship,description,"
            "link_user_website(),title,pinned_to_board,is_cpc_ad,image_signature,alt_text,visual_objects(),mobile_link,dpa_creative_type,"
            "is_visualization_enabled,third_party_pin_owner,creator_analytics,is_eligible_for_cutout_tool,ip_eligible_for_stela,"
            "highlighted_did_it,via_pinner,comment_reply_comment_id,shuffle(),is_translatable,videos(),attribution,"
            "canonical_merchant_domain,top_interest,category,is_virtual_try_on}",
            "user.{country,gender,type,age_in_years,follower_count,explicitly_followed_by_me,is_default_image,is_under_16,is_under_18,"
            "save_behavior,verified_domains,is_ads_only_profile,is_partner,verified_identity,id,comments_disabled,is_verified_merchant,"
            "first_name,should_default_comments_off,ads_only_profile_site,show_creator_profile,is_primary_website_verified,last_name,"
            "blocked_by_me,avatar_color_index,is_private_profile,custom_gender,partner(),full_name,website_url,allow_idea_pin_downloads,"
            "image_large_url,image_medium_url,username,should_show_messaging,vto_beauty_access_status}",
            "board.{has_custom_cover,image_thumbnail_url,is_collaborative,collaborating_users(),created_at,privacy,type,is_ads_only,url,"
            "image_cover_url,layout,collaborated_by_me,should_show_board_collaborators,tracking_params,owner(),name,"
            "collaborator_invites_enabled,is_featured_for_active_campaign,action,section_count,id,category}",
            "video.{duration,id,video_list[V_HLSV3_MOBILE, V_DASH_HEVC]}",
            "shuffleasset.{shuffle_item_image,item_type,id,bitmap_mask,type,pin(),mask}",
            "shuffleitem.{template_config,shuffle_item_image(),pin,offset,effect_data,item_type,rotation,scale,id,text,shuffle_asset,mask}",
            "richpinproductmetadata.{label_info,offers,additional_images,has_multi_images,shipping_info,offer_summary,item_set_id,item_id,"
            "name,id,type,brand}",
            "aggregatedpindata.{comment_count,is_shop_the_look,has_xy_tags,pin_tags,did_it_data,slideshow_collections_aspect_ratio,"
            "aggregated_stats,is_stela,id,pin_tags_chips}",
            "shuffle.{parent(),is_promoted,canonical_pin,items(),effect_data,user(),is_remixable,created_at,images[236x],tracking_params,"
            "updated_at,source_app_type_detailed,id,root(),posted_at}",
            "pin.images[200x,236x,736x,136x136,474x]",
            "makecardtutorialinstructionview.images[236x,736x]",
            "shuffleasset.cutout_images[originals]",
            "makecardtutorialview.images[236x,736x]",
            "shuffleitem.images[736x,365x]"
        ]

        params = {
            "fields": ",".join(fields),
            "client_tracking_params": "CwABAAAAEDg3MTE5MDU3MjY3NjQ4NTAKAAIAAAGWBil1tQYAAwAACgAGAAAAAAAAACQLAAcAAAAKbmdhcGkvcHJvZAsACAAAACAwYmFmOGRmZjdlMWJkNjM4OWJmMTRhYjQwZAA",
            "view_type": view_type,
            "view_parameter": view_parameter
        }

        return self._handle_request(
            method="GET",
            endpoint=f"/pins/{pin_id}/",
            params=params
        )


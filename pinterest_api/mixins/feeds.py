from typing import Dict, Any, List, Optional
import requests
import random
from ..exceptions import LoginFailedError

class FeedsMixin:
    """Mixin for Pinterest feed-related functionality."""

    def get_home_feed(
        self,
        page_size: int = 25,
        dynamic_grid_stories: int = 6,
        view_type: int = 24,
        view_parameter: int = 261,
        item_count: int = 0,
        network_bandwidth_kbps: int = 39820,
        connection_type: int = 3,
        in_nux: bool = True,
        in_local_navigation: bool = False,
        link_header: int = 7,
        video_autoplay_disabled: int = 0,
        bookmark: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the user's home feed from Pinterest.
        
        Args:
            page_size (int): Number of items per page
            dynamic_grid_stories (int): Number of dynamic grid stories
            view_type (int): View type parameter
            view_parameter (int): View parameter value
            item_count (int): Initial item count
            network_bandwidth_kbps (int): Network bandwidth in kbps
            connection_type (int): Connection type identifier
            in_nux (bool): Whether in new user experience
            in_local_navigation (bool): Whether in local navigation
            link_header (int): Link header value
            video_autoplay_disabled (int): Video autoplay disabled flag
            bookmark (str, optional): Bookmark token for pagination
            
        Returns:
            Dict[str, Any]: Feed data including pins and related information
            
        Raises:
            LoginFailedError: If not logged in or access token is missing
            requests.exceptions.RequestException: For network/API errors
        """
        if not hasattr(self, 'get_access_token'):
            raise LoginFailedError("Login mixin not properly initialized")
            
        # Device info parameters
        device_info = {
            "java_heap_space": "512MB",
            "image_width": "236x"
        }
        
        # Standard Pinterest fields for feed data
        fields = (
            "pin.{comment_count,is_eligible_for_related_products,native_pin_stats,type,"
            "id,ad_destination_url,rich_summary(),grid_title,native_creator(),is_native,"
            "has_displayable_community_content,unified_user_note,has_variants,is_premiere,section(),"
            "done_by_me,is_instagram_api,is_oos_product,reaction_by_me,dominant_color,formatted_description,"
            "pin_note(),domain,did_it_disabled,is_stale_product,media_attribution(),is_v1_idea_pin,"
            "favorite_user_count,collection_pin(),shopping_mdl_browser_type,ad_data(),created_at,tracked_link,"
            "highlighted_aggregated_comments,is_scene,total_reaction_count,is_eligible_for_aggregated_comments,"
            "tracking_params,digital_media_source_type_label,is_eligible_for_pdp,closeup_unified_description,"
            "is_unsafe_for_comments,is_call_to_create,promoter(),reaction_counts,should_open_in_stream,is_repin,"
            "aggregated_pin_data(),should_mute,story_pin_data(),board(),is_whitelisted_for_tried_it,closeup_attribution,"
            "shopping_flags,pinner(),story_pin_data_id,favorited_by_me,comments_disabled,cacheable_id,origin_pinner(),"
            "user_mention_tags,rich_metadata(),closeup_description,is_video,can_delete_did_it_and_comments,"
            "call_to_action_text,link_domain(),canonical_merchant_name,music_attributions,is_promoted,"
            "board_conversation_thread,hashtags,link,sponsorship,description,link_user_website(),title,"
            "pinned_to_board,image_signature,alt_text,visual_objects(),mobile_link,is_visualization_enabled,"
            "third_party_pin_owner,creator_analytics,is_eligible_for_cutout_tool,ip_eligible_for_stela,"
            "highlighted_did_it,via_pinner,comment_reply_comment_id,is_translatable,videos(),attribution,"
            "canonical_merchant_domain,top_interest,category,is_virtual_try_on},"
            "pin.images[200x,236x,736x,136x136,474x],"
            "aggregatedpindata.{comment_count,is_shop_the_look,has_xy_tags,pin_tags,did_it_data,slideshow_collections_aspect_ratio,"
            "aggregated_stats,is_stela,id,pin_tags_chips}"
        )
        
        params = {
            'in_nux': str(in_nux).lower(),
            'item_count': item_count,
            'network_bandwidth_kbps': network_bandwidth_kbps,
            'device_info': str(device_info).replace("'", '"'),
            'connection_type': connection_type,
            'in_local_navigation': str(in_local_navigation).lower(),
            'link_header': link_header,
            'video_autoplay_disabled': video_autoplay_disabled,
            'fields': fields,
            'dynamic_grid_stories': dynamic_grid_stories,
            'page_size': page_size,
            'view_type': view_type,
            'view_parameter': view_parameter
        }

        # Add bookmark for pagination if provided
        if bookmark:
            params['bookmarks'] = [bookmark]
        
        return self._handle_request(
            method="GET",
            endpoint="/feeds/home/",
            params=params
        )

    def extract_pins_from_feed(self, feed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract pins from feed response data.
        
        Args:
            feed_data (Dict[str, Any]): Response from get_home_feed
            
        Returns:
            List[Dict[str, Any]]: List of pin data objects
        """
        pins = []
        try:
            # Extract pins from feed response
            if isinstance(feed_data, dict):
                # Get bookmark for next page if available
                self._last_bookmark = feed_data.get('bookmark')
                
                # Extract pins from items
                items = feed_data.get('data', [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            # Each item in the feed is already a pin with aggregated_pin_data
                            if item.get('type') == 'pin' and item.get('id'):
                                pins.append(item)
        except Exception as e:
            print(f"Error extracting pins from feed: {str(e)}")
        
        return pins

    def get_random_pin_from_feed(self, feed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get a random pin from feed data.
        
        Args:
            feed_data (Dict[str, Any]): Response from get_home_feed
            
        Returns:
            Optional[Dict[str, Any]]: Random pin data or None if no pins found
        """
        pins = self.extract_pins_from_feed(feed_data)
        return random.choice(pins) if pins else None 
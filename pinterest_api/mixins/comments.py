from typing import Dict, Optional, Any

class CommentMixin:
    """Mixin for Pinterest comment-related operations."""

    def post_comment(
        self,
        pin_data: Dict[str, Any],
        text: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """Post a comment on a Pinterest pin.

        Args:
            pin_data (Dict[str, Any]): The pin data containing id and aggregated_pin_data
            text (str): The comment text
            force (bool, optional): Force flag. Defaults to False.

        Returns:
            Dict[str, Any]: Response from the API containing comment details
        """
        endpoint = f"/aggregated_pin_data/{pin_data['aggregated_pin_data']['id']}/comment/"
        
        # Fields to request in the response
        fields = "aggregatedcomment.{comment_count,user(),created_at,is_edited,text,type,pin(),id}"

        # Request headers
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Request data as form-urlencoded
        data = {
            "fields": fields,
            "text": text,
            "pin": pin_data['id'],
            "force": str(force).lower()
        }

        return self._handle_request(
            method="POST",
            endpoint=endpoint,
            data=data,
            headers=headers
        ) 
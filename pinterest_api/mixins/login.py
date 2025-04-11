from typing import Dict, Any
import requests
from ..exceptions import LoginFailedError, InvalidResponseError, IncorrectPasswordError, PasswordResetedError

class LoginMixin:
    # Additional headers specific to login
    LOGIN_HEADERS = {
        'X-Pinterest-Advertising-Id': 'ef8cf8e9-183e-4fb9-9a21-fdb0cfb9a586',
        'X-Pinterest-Device-Hardwareid': '0b55536e926ec0af',
        'X-Pinterest-Installid': '9f903b10747e4bdb88e754599182eaf'
    }

    def __init__(self):
        """Initialize login-related attributes."""
        self._user_data = None
        self._access_token = None

    def login(self) -> Dict[str, Any]:
        """
        Login to Pinterest.
        
        Returns:
            Dict[str, Any]: User data and authentication tokens
            
        Raises:
            IncorrectPasswordError: If the password is incorrect
            LoginFailedError: If login fails for other reasons
            InvalidResponseError: If response format is invalid
            PasswordResetedError: If Pinterest has reset the account's password
            requests.exceptions.RequestException: For network/API errors
        """
        endpoint = "/login/"
        timestamp = self._get_timestamp()
        
        # Standard Pinterest fields for login
        fields = (
            "user.{owners(),country,businesses(),is_country_eligible_for_lead_form_autofill,"
            "about,is_gender_eligible_for_lead_form_autofill,type,age_in_years,"
            "is_default_image,is_under_16,is_under_18,connected_to_etsy,pin_count,"
            "is_partner,is_parental_control_passcode_enabled,id,resurrection_info,"
            "secret_board_count,show_creator_profile,is_age_eligible_for_lead_form_autofill,"
            "ccpa_opted_out,parental_control_anonymized_email,custom_gender,partner(),"
            "profile_cover(),full_name,following_count,connected_to_youtube,image_large_url,"
            "dsa_opted_out,board_count,third_party_marketing_tracking_enabled,"
            "vto_beauty_access_status,is_candidate_for_parental_control_passcode,"
            "is_name_eligible_for_lead_form_autofill,gender,created_at,"
            "personalize_from_offsite_browsing,follower_count,image_xlarge_url,"
            "most_recent_board_sort_order,ads_customize_from_conversion,save_behavior,"
            "first_name,has_catalog,email,exclude_from_search,should_default_comments_off,"
            "live_creator_type,last_name,interest_following_count,avatar_color_index,"
            "is_private_profile,is_email_eligible_for_lead_form_autofill,is_employee,"
            "connected_to_instagram,login_state,connected_to_facebook,location,"
            "image_medium_url,username,should_show_messaging},"
            "profilecoversource.{video(),source_id,source,images[1200x]},"
            "video.{duration,signature,id,video_list[V_HLSV3_MOBILE, V_DASH_HEVC]}"
        )
        
        # Default token for login
        token = (
            "%7B%22token%22%3A%2203AFcWeA4eiNeRg1B3K0zpCgPnV1GcYg72CHWcjwEwulhFkauTT2lA1xCySPk9d-O-"
            "Jk4vV6VRH7bdNNKN4VJLzEnuRDu3B0Rr3fKukZ_FqEzsQMSTOXPey_Ly4E0ZdP3E8f-xPpWLtcrA9RKkNOBZs23"
            "ijjpvyYUt7tWHlAHJAHQE8EOnNGI6nJL4LaTbry1rQcrkaApU1Oo581Y_pvQsij-pQL7Bzzv4Q3PaOqvOmMy_WK"
            "T7fcCx0gfQw86aumFO7eb9ODAIr1i_XnT8EiS9wSFqI8khylS96Jlt6I3S0Hh1v-MkpTSLHvFyP2fGJ1Q_dSuXk"
            "YxNiOYYPnWtLAEfD_4fim36RQ7puamPJKRDamHZMDVPAf9NPw41th8-UFOvzuEByXtyI1PtZvf26807SFeys3VJI"
            "crQUkRF6165Q4TV_HOQ59ROd1fJ4NU2ug9j2KYNvXRj6vyK5PXKyI28yl5tOoRbFTVdWQK0aAi-Vsycm08_Yrbm"
            "tRTP5Gs0aqc9-WTZioR5M6EghFTJiDHaIbiK9akqtWcSaCyexac4AT2ZUUsaCJJIQ552ngcmWO5l-e9P3KeuIVd"
            "8yBaqlHTwmKLA5d5AW8rqyc7ZlON45WSvMBc7O-SPnVQKGMcOD99Wfeql_1kRxpmr2bTXVXUFwx0GZE_pPCmZBX"
            "9fwef-wsyK3u_p5bW3ruvae1FEsbdrYCkxhcfdXnvy90tCt1v77tEBsWuby4DvBvS3qvJ_7J2a6u389GyTzqYqm"
            "1wWpWOM7YTCysgqtDGEH2xWRasfp7nSMEx8HKQa-lOBHq-P0s7AR1FCC8rigB8qzEC0rc5159K_LT0oGJCMfb0J"
            "daJUIJSMA1tR45OzpvJuvYPMQWgYYdjCYfttH6yoBjNkEVXfzo6ZmSGJC9JWSycZQhklfj5lFKOBS2TpRA8iUQ_"
            "baHJJGxpL9iynqy41KfjGma9MMwpDPYl81cSzwF0Ew46WhLjLi97jOQUtENz2w6FiWpggzljTom5Yl4nyptzsKX"
            "8rzd7OhKB3KhWxWIqW2StYdunjASdiMXBpfrUcxKam5liQ9fncWl9_BWc6UInVVMMKjzs3IO2b3ypWSA5txzoY8"
            "_88PfV7l8UF8HQA8jRMN-Ht8SYHTpi1wmKGnU8OO0hAAR_8lBKbu2hQQ18BHjgVSW4V57rWD-9mFCbqz4fzOMiJ"
            "MWWcO1zRd_vlvY0f69-jJ8LsMYplYXJihWKEGANNIJjriQbGwppgke0PwKABy0NnHhsx9sP1uHo8j4nVT4OL0L"
            "dItUf8aCs0GjpIzxzW2ssE9fzljAoIB3OgkgPJkiAP5Wbw7pNY4bGX5l9sFwgEgdV-4Sk_lDoud89zW-3veXV4u"
            "tPBTuVvYVd0c28UrFFue-Rim3FVzWiKCKl8NkGN3nAdBFOSDyU6d71NOri6bTqFzZj6KZiNygDPh0HP-BRBJ6Q2"
            "MHDDDk_EEs69tZZk_4951nIzF4BMq_cqYkWr5mV0n0fM0q4KlfPgpNbHlKn4YGca3p5SLVfW2Oc5HFjMqKbRnRM"
            "RGZdCCZh9jwSgqvq4I4wkVFdHsEoyJyaRhNtdHwVQBg6timm4ISXNfxE4Xga3S5x5Q0d8OTPo6jMLsERC7Z_D2C"
            "Ee4wXFMkPEDzqaw_uwZNa0GrGyonFvwCG_5PXQqouC26QUTEH_BaPyeYSoDJeZ_TMc2TsEkusQp40LxMvRj10-y"
            "2gMjid8faOBT7C1hV05f96ZrVTHFFS_xgvHXFkHOZUkybUj0zUUlRnW11Nf17oKUXmaICBjXsRZ8LwoN6I34jZd"
            "hctD2QOf0x9WdqZI6izRUCcEAz_I1WuC3-4oAdDTXB3OO9ALdnQerVcT67WrboH0MMHk4d5IBo-4oHk9Ovix7us"
            "8wtLJgVWycOOMmKOGu_ePWMOaSj0-RKqSAc-UslmbQ0q0kG9Totf9IYDpk8grEOwcxB4yBuPsNL0-4kosGwWoY3"
            "qo-P-5cpOFDols-a5"
        )
        
        form_data = {
            'fields': fields,
            'username_or_email': self.email,
            'password': self.password,
            'token': token
        }
        
        params = {
            'client_id': self.CLIENT_ID,
            'timestamp': timestamp
        }
        
        raw_form_data = '&'.join(f"{k}={v}" for k, v in form_data.items())
        signature, _ = self.generate_login_signature(
            "POST",
            f"{self.BASE_URL}{endpoint}?client_id={self.CLIENT_ID}&timestamp={timestamp}",
            raw_form_data
        )
        
        params['oauth_signature'] = signature
        
        try:
            data = self._handle_request(
                method="POST",
                endpoint=endpoint,
                data=form_data,
                params=params,
                headers=self.LOGIN_HEADERS,
                require_auth=False
            )
            
            # Validate response format
            if not isinstance(data, dict) or 'status' not in data or 'data' not in data:
                raise InvalidResponseError(data)

            if data['status'] != 'success':
                # Check for specific error codes
                error_code = data.get('code')
                if error_code == 78 or error_code == 85:
                    raise IncorrectPasswordError()
                elif error_code == 88:
                    raise PasswordResetedError("Pinterest has reset your password for security reasons. Please reset your password at https://www.pinterest.com/password/reset/")
                error_msg = data.get('message', 'Unknown error')
                raise LoginFailedError(error_msg)
            
            # Store user data and access token
            self._user_data = data['data']['user']
            self._access_token = data['data'].get('v5_access_token')
            
            return True
            
        except requests.exceptions.RequestException as e:
            raise LoginFailedError(f"Login request failed: {str(e)}")

    def get_user_data(self) -> Dict[str, Any]:
        """
        Get the stored user data.
        
        Returns:
            Dict[str, Any]: User data from the last successful login
            
        Raises:
            LoginFailedError: If no user data is available (not logged in)
        """
        if self._user_data is None:
            raise LoginFailedError("No user data available. Please login first.")
        return self._user_data

    def get_access_token(self) -> str:
        """
        Get the stored access token.
        
        Returns:
            str: Access token from the last successful login
            
        Raises:
            LoginFailedError: If no access token is available (not logged in)
        """
        if self._access_token is None:
            raise LoginFailedError("No access token available. Please login first.")
        return self._access_token

import scrapy
from scrapy.http import HtmlResponse
import re
import json
from urllib.parse import urlencode
from copy import deepcopy
from inst.items import InstItem

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    inst_login = 'viktorvin28'
    inst_password = '********'
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    target_inst = ['babydov', 'el_mblk']
    graphql_url = 'https://www.instagram.com/graphql/query/?'
    followers_query_hash = 'c76146de99bb02f6415203be841dd25a'
    following_query_hash = 'd04b0a864b4b54837c0d870b0e77e076'

    def parse(self, response: HtmlResponse):
        csrf = self.fetch_craft_token(response.text)
        yield scrapy.FromRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={'inst_login': self.inst_login,
                      'inst_password': self.inst_password},
            headers={'X-CSRFToken': csrf}
        )

    def login(self, response:HtmlResponse):
        auto_login = json.loads(response.text)
        if auto_login['authenticated']:
            for inst_login in self.target_inst:
                yield response.follow(
                    f'/{inst_login}/',
                    callback=self.user_parse,
                    cd_kwargs={'inst_login': self.target_inst}
                )

    def user_parse(self, responce: HtmlResponse, inst_login):
        user_id = self.fetch_user_id(responce.text, inst_login)
        variables = {
            'id': user_id,
            'include_reel': True,
            'fetch_mutual': True,
            'first': 24
        }

        yield responce.follow(
            f'{self.graphql_url}query_hash={self.followers_query_hash}&{urlencode(variables)}',
            callback=self.followers_parse,
            cb_kwargs={
                'inst_login': inst_login,
                'user_id': user_id,
                'variables': deepcopy(variables)
            }
        )

    def follow_parse(self, response: HtmlResponse, inst_login, user_id, variables):
        follow_json = json.loads(response.text)
        page_info = follow_json.get('data').get('user').get('edge_follower_by').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info['end_cursor']
            follow_url = f'{self.graphql_url}query_hash={self.followers_query_hash}&{urlencode(variables)}'
            yield response.follow(
                follow_url,
                callback=self.followers_parse,
                cb_kwargs={
                    'inst_login': inst_login,
                    'user_id': user_id,
                    'variables': deepcopy(variables)
                }
            )

        followers = follow_json.get('data').get('user').get('edge_follower_by').get('edges')
        for follower in followers:
            profile = {
                '_id': user_id + '_' + follower['node']['id'],
                '_collection': 'followers',
                'id': follower['node']['id'],
                'username': follower['node']['username'],
                'full_name': follower['node']['full_name'],
                'profile_pic_url': follower['node']['profile_pic_url'],
                'is_private': follower['node']['is_private'],
                'is_verified': follower['node']['is_verified'],
                'linked_user_id': user_id,
                'linked_username': inst_login
            }

            yield InstItem(**profile)
    def follow_parse(self, responce: HtmlResponse, inst_login, user_id, variables):
        follower_json = json.loads(responce.text)
        page_info = follower_json.get('data').get('user').get('edge_follow').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info['end_cursor']
            follower_url = f'{self.graphql_url}query_hash={self.followers_query_hash}&{urlencode(variables)}'

            yield responce.follow(
                follower_url,
                callback=self.follow_parse(),
                cb_kwargs={
                    'inst_login': inst_login,
                    'user_id': user_id,
                    'variables': deepcopy(variables)
                }
            )

        follower = follower_json.get('data').get('user').get('edge_follow').get('edges')
        for following in follower:
            profile = {
                '_id': user_id + '_' + following['node']['id'],
                '_collection': 'followings',
                'id': following['node']['id'],
                'username': following['node']['username'],
                'full_name': following['node']['full_name'],
                'profile_pic_url': following['node']['profile_pic_url'],
                'is_private': following['node']['is_private'],
                'is_verified': following['node']['is_verified'],
                'linked_user_id': user_id,
                'linked_username': inst_login
            }
            yield InstItem(**profile)


    def fetch_craft_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, inst_login):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % inst_login, text
        ).group()
        return json.loads(matched).get('id')

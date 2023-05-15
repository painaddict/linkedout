import sys, json, time
import copy
import base64, gzip
import requests
import datetime
from loguru import logger
import config

class Linkedout(object):
	def __init__(self, slug):
		self.session = requests.Session()
		self.session.headers.update(config.HEADERS)
		self.session.cookies.update(config.COOKIES)
		self.course_slug = slug
		self.check_validity() # check if cookies are valid

		self.get_course_details()
		self.parse_course()
	
	def get_course_details(self):
		self.course_json = json.loads(self.session.get(url=config.BASE_URL + 'detailedLearningPaths', params={
    		'learningPathSlug': self.course_slug,
    		'q': 'slug',
    		'version': '2',
		}, headers={
			'accept': 'application/vnd.linkedin.normalized+json+2.1' # will not return 'included' without this header
		}).content)

	def check_validity(self):
		s = self.session.get(url=config.BASE_URL + 'me', params={
				'q': 'inProgress'
			})
		if 'CSRF' in s.text:
			logger.error('Incorrect credentials! Please ensure CSRF token matches JSESSIONID')
			sys.exit(1)
	
	def parse_course(self):
		# if '404' in json.dumps(self.course_json):
		# 	logger.error("Improper slug!")
		# 	sys.exit(1) 

		self.course_title = self.course_json['data']['elements'][0]['title']
		self.duration = str(datetime.timedelta(seconds = self.course_json['data']['elements'][0]['contentDurationInSeconds']))
		logger.info("Course Name: " + self.course_title)
		logger.info("Duration: " + self.duration)

		for card in self.course_json['included']:
			if card['$type'] == 'com.linkedin.learning.api.common.Card':
				logger.info('Course found: ' + card['headline']['title']['text'] + ' -- ' +  
							str(datetime.timedelta(seconds = card['length']['duration'])))
				self.get_deco_details(card['slug'])

	def get_deco_details(self, slug):
		deco_json = self.session.get(url=config.BASE_URL + 'courses', params={
				'decorationId': 'com.linkedin.learning.api.deco.content.DecoratedCourse-96',
				'q': 'slug',
				'slug': slug
			}, headers={
				'accept': 'application/vnd.linkedin.normalized+json+2.1' # will not return 'included' without this header
			}).json()
		
		# indexing the completed videos
		
		completed_videos = []
		for video in deco_json['included']:
			if video['$type'] == 'com.linkedin.learning.api.interaction.ConsistentBasicVideoViewingStatus':
				if video['details'] is not None:
					if video['details']['statusType'] == 'COMPLETED':
						completed_videos.append(video['cachingKey'])
		
		for video in deco_json['included']:
			if video['$type'] == 'com.linkedin.learning.api.deco.content.Video':
				if video['*lyndaVideoViewingStatus'] not in completed_videos:
					logger.debug('Watching ' + video['title'] + ' ...')
					self.parse_video(video['slug'], slug)

	def parse_video(self, slug, parent_slug):
		video_json = self.session.get(url=config.BASE_URL + 'videos', params={
				'decorationId': 'com.linkedin.learning.api.deco.content.DecoratedVideo-58',
				'parentSlug': parent_slug,
				'q': 'slugs', # plural
				'slug': slug
			}, headers={
				'accept': 'application/vnd.linkedin.normalized+json+2.1' # will not return 'included' without this header
			}).json()
		self.watch_video(video_json)

	def watch_video(self, video_json): # where the magic happens
		
		def timex():
			return int(time.time() * 1000)

		for element in video_json['included']:
			if element.get('$type') == 'com.linkedin.learning.api.deco.content.Video':
				application_viewer_urn = 'urn:li:enterpriseProfile:(urn:li:enterpriseAccount:92961692,180890037)'
				video_length = int(element['duration']['duration'])
				media_tracking_id = element['trackingId']
				tracking_id = element['presentation']['videoPlay']['videoPlayMetadata']['trackingId']
				object_urn = element['trackingUrn']
				media_url = element['presentation']['videoPlay']['videoPlayMetadata']['adaptiveStreams'][0]['masterPlaylists'][0]['url']

		media_tracking_id_array = []
		for x in base64.b64decode(media_tracking_id):
			media_tracking_id_array.append(int(oct(x).replace('0o', '')))
				
		init_post_json = [{
			'eventBody': {
				'mobileHeader': None,
				'mediaHeader': {
					'deliveryMode': 'PROGRESSIVE',
					'playerType': 'HTML5',
					'mediaType': 'VIDEO',
					'accountAccessType': 'ENTERPRISE',
					'mediaSource': 'learning'
				},
				'mediaTrackingObject': {
					'objectUrn': object_urn,
					'trackingId': tracking_id
				},
				'initializationStartTime': timex(),
				'duration': video_length,
				'mediaLiveState': 'PRE_RECORDED',
				'header': {
					'pageInstance': {
						'pageUrn': 'urn:li:page:d_learning_content',
						'trackingId': media_tracking_id
					},
					'time': timex(),
					'version': config.VERSION,
					'server': '',
					'service': '',
					'guid': 'random', # ????
					'memberId': 0,
					'applicationViewerUrn': application_viewer_urn,
					'clientApplicationInstance': {
						'applicationUrn': 'urn:li:application:(learning-web,learning-web)',
						'version': config.VERSION,
						'trackingId': media_tracking_id_array # octal array of base-64 tracking id
					}
				},
				'requestHeader': {
					'interfaceLocale': 'en_US',
					'pageKey': 'd_learning_content',
					'path': '/learning/creating-a-business-plan-2/what-is-a-business-plan', # does this matter?
					'referer': 'https://www.linkedin.com/learning-login/b2c/login',
					'isFlushOnCloseBrowserTabEnabled': True,
					'isBrowserPersistentRetryEnabled': False,
					'trackingCode': 'd_learning_content'
				}
			},
			'eventInfo': {
				'appId': 'com.linkedin.web.learning',
				'eventName': 'MediaInitializationStartEvent',
				'topicName': 'MediaInitializationStartEvent',
				'shouldAnonymizeMemberId': True
			}
		},
		{
			'eventBody': {
				'contentTrackableObject': {
					'objectUrn': object_urn,
					'trackingId': tracking_id
				},
				'header': {
					'pageInstance': {
						'pageUrn': 'urn:li:page:d_learning_content',
						'trackingId': media_tracking_id
					},
					'time': timex(),
					'version': config.VERSION,
					'server': '',
					'service': '',
					'guid': 'random', # ????
					'memberId': 0,
					'applicationViewerUrn': application_viewer_urn,
					'clientApplicationInstance': {
						'applicationUrn': 'urn:li:application:(learning-web,learning-web)',
						'version': config.VERSION,
						'trackingId': media_tracking_id_array # octal array of base-64 tracking id
					}
				},
				'requestHeader': {
					'interfaceLocale': 'en_US',
					'pageKey': 'd_learning_content',
					'path': '/learning/creating-a-business-plan-2/what-is-a-business-plan', # does this matter?
					'referer': 'https://www.linkedin.com/learning-login/b2c/login',
					'isFlushOnCloseBrowserTabEnabled': True,
					'isBrowserPersistentRetryEnabled': False,
					'trackingCode': 'd_learning_content'
				}
			},
			'eventInfo': {
				'appId': 'com.linkedin.web.learning',
				'eventName': 'LearningContentViewEvent',
				'topicName': 'LearningContentViewEvent',
				'shouldAnonymizeMemberId': True
			}
		}]

		buffering_post_json = [{
			'eventBody': {
				'mobileHeader': None,
				'mediaHeader': {
					'deliveryMode': 'PROGRESSIVE',
					'playerType': 'HTML5',
					'mediaType': 'VIDEO',
					'accountAccessType': 'ENTERPRISE',
					'mediaSource': 'learning'
				},
				'mediaTrackingObject': {
					'objectUrn': object_urn,
					'trackingId': tracking_id
				},
				'mediaLiveState': None,
				'bufferingType': 'INIT',
				'initializationStartTime': timex(),
				'bufferingStartTime': timex(),
				'header': {
					'pageInstance': {
						'pageUrn': 'urn:li:page:d_learning_content',
						'trackingId': media_tracking_id
					},
					'time': timex(),
					'version': config.VERSION,
					'server': '',
					'service': '',
					'guid': 'random', # ????
					'memberId': 0,
					'applicationViewerUrn': application_viewer_urn,
					'clientApplicationInstance': {
						'applicationUrn': 'urn:li:application:(learning-web,learning-web)',
						'version': config.VERSION,
						'trackingId': media_tracking_id_array # octal array of base-64 tracking id
					}
				},
				'requestHeader': {
					'interfaceLocale': 'en_US',
					'pageKey': 'd_learning_content',
					'path': '/learning/creating-a-business-plan-2/what-is-a-business-plan', # does this matter?
					'referer': 'https://www.linkedin.com/learning-login/b2c/login',
					'isFlushOnCloseBrowserTabEnabled': True,
					'isBrowserPersistentRetryEnabled': False,
					'trackingCode': 'd_learning_content'
				}
			},
			'eventInfo': {
				'appId': 'com.linkedin.web.learning',
				'eventName': 'MediaBufferingStartEvent',
				'topicName': 'MediaBufferingStartEvent',
				'shouldAnonymizeMemberId': True
			}
		}]

		complete_post_json = [{
			'eventBody': {
				'contentProgressState': 'COMPLETED',
				'previousContentProgressState': 'IN_PROGRESS',
				'contextTrackingId': tracking_id,
				'createdTime': timex(),
				'durationInSecondsViewed': video_length,
				'mediaTrackingObject': {
					'objectUrn': object_urn,
					'trackingId': tracking_id
				},
				'playerState': {
					'bitrate': None,
					'casting': 'NOT_MEASURED',
					'ccVisible': 'OFF',
					'downloaded': 'NOT_MEASURED',
					'fullScreen': 'OFF',
					'isAudioOnly': False,
					'isPlaying': True,
					'isVisible': True,
					'length': video_length,
					'speed': 1,
					'timeElapsed': video_length,
					'volume': 100,
					'mediaUrl': media_url,
					'mediaLiveState': 'PRE_RECORDED'
				},
				'videoProgressStateMetric': 'NON_SCRUB_VIDEO_TIME_WATCHED',
				'header': {
					'pageInstance': {
						'pageUrn': 'urn:li:page:d_learning_content',
						'trackingId': media_tracking_id
					},
					'time': timex(),
					'version': config.VERSION,
					'server': '',
					'service': '',
					'guid': 'random', # ????
					'memberId': 0,
					'applicationViewerUrn': application_viewer_urn,
					'clientApplicationInstance': {
						'applicationUrn': 'urn:li:application:(learning-web,learning-web)',
						'version': config.VERSION,
						'trackingId': media_tracking_id_array # octal array of base-64 tracking id
					}
				},
				'requestHeader': {
					'interfaceLocale': 'en_US',
					'pageKey': 'd_learning_content',
					'path': '/learning/creating-a-business-plan-2/what-is-a-business-plan', # does this matter?
					'referer': 'https://www.linkedin.com/learning-login/b2c/login',
					'isFlushOnCloseBrowserTabEnabled': True,
					'isBrowserPersistentRetryEnabled': False,
					'trackingCode': 'd_learning_content'
				}
			},
			'eventInfo': {
				'appId': 'com.linkedin.web.learning',
				'eventName': 'LearningContentClientProgressStateChangeEvent',
				'topicName': 'LearningContentClientProgressStateChangeEvent',
				'shouldAnonymizeMemberId': True
			}
		}]

		in_progress_post_json = copy.deepcopy(complete_post_json)
		in_progress_post_json[0]['eventBody']['contentProgressState'] = 'IN_PROGRESS'
		in_progress_post_json[0]['eventBody']['previousContentProgressState'] = None	

		init_end_post_json = copy.deepcopy(init_post_json)
		init_end_post_json[0]['eventInfo']['eventName'] = 'MediaInitializationEndEvent'
		init_end_post_json[0]['eventInfo']['topicName'] = 'MediaInitializationEndEvent'

		s = self.session.post(url=config.TRACK_URL, data=json.dumps(init_post_json), headers={
				"Accept-Language": "en-US,en;q=0.9",
				"content-type": "text/plain;charset=UTF-8"
			})
		print(s.status_code)
		print(s.request.body)

		s = self.session.post(url=config.TRACK_URL, data=json.dumps(init_end_post_json), headers={
				"Accept-Language": "en-US,en;q=0.9",
				"content-type": "text/plain;charset=UTF-8"
			})
		print(s.status_code)
		print(s.request.body)

		s = self.session.post(url=config.TRACK_URL, data=json.dumps(buffering_post_json), headers={
				"Accept-Language": "en-US,en;q=0.9",
				"content-type": "text/plain;charset=UTF-8"
			})
		print(s.content)
		print(s.status_code)
		print(s.request.body)

		s = self.session.post(url=config.TRACK_URL, data=json.dumps(in_progress_post_json), headers={
				"Accept-Language": "en-US,en;q=0.9",
				"content-type": "text/plain;charset=UTF-8"
			})
		print(s.status_code)
		print(s.request.body)

		s = self.session.post(url=config.TRACK_URL, data=json.dumps(complete_post_json), headers={
				"Accept-Language": "en-US,en;q=0.9",
				"content-type": "text/plain;charset=UTF-8"
			})
		print(s.status_code)
		print(s.request.body)


@logger.catch
def main():
	if len(sys.argv) < 2:
		logger.error("Course slug not specified!")
		return
	slug = sys.argv[1]
	linkedout = Linkedout(slug)

if __name__ == "__main__":
	main()
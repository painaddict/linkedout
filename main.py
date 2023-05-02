import sys, json
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
			'accept': 'application/vnd.linkedin.normalized+json+2.1' # will not return 'includes' without this header
		}).content)

	def check_validity(self):
		s = self.session.get(url=config.BASE_URL + 'me', params={
				'q': 'inProgress'
			})
		if 'CSRF' in s.text:
			logger.error('Incorrect credentials! Please ensure CSRF token matches JSESSIONID')
			sys.exit(1)
	
	def parse_course(self):
		if '404' in json.dumps(self.course_json):
			logger.error("Improper slug!")
			sys.exit(1)

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
				'accept': 'application/vnd.linkedin.normalized+json+2.1'
			}).json()
		for video in deco_json['included']:
			if video['$type'] == 'com.linkedin.learning.api.deco.content.Video':
				logger.debug('Watching ' + video['title'])

@logger.catch
def main():
	if len(sys.argv) < 2:
		logger.error("Course slug not specified!")
		return
	slug = sys.argv[1]
	linkedout = Linkedout(slug)

if __name__ == "__main__":
	main()
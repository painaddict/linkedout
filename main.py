import sys, json
import requests
from loguru import logger
import config

class Linkedout(object):
	def __init__(self, slug):
		self.session = requests.Session()
		self.session.headers.update(config.HEADERS)
		self.session.cookies.update(config.COOKIES)
		self.slug = slug
		self.check_validity()
	
	def get_course_details(self):
		s = self.session.get(url=config.BASE_URL + 'detailedLearningPaths', params={
    		'learningPathSlug': self.slug,
    		'q': 'slug',
    		'version': '2',
		}).json()
		logger.info(s)

	def check_validity(self):
		s = self.session.get(url=config.BASE_URL + 'me', params={
				'q': 'inProgress'
			})
		if 'CSRF' in s.text:
			logger.error("Incorrect credentials! Please ensure CSRF token matches JSESSIONID")
			sys.exit(1)
		

@logger.catch
def main():
	if len(sys.argv) < 2:
		logger.error("Course slug not specified!")
		return
	slug = sys.argv[1]
	linkedout = Linkedout(slug)

if __name__ == "__main__":
	main()